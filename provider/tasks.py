"""
Celery tasks for asynchronous submission processing.
Contains some hard-coded A+ specific stuff that should be generalized.
"""

import json

from django.conf import settings
import celery
from celery.utils.log import get_task_logger

import requests

from data.models import Course, Exercise, TaskError
from matcher import tasks as matcher_tasks
from provider import aplus
from provider.insert import (
    submission_exists,
    insert_submission,
    prepare_submission,
    InsertError,
)
import radar.config as config_loaders
from radar.settings import DEBUG, CELERY_DEBUG


logger = get_task_logger(__name__)


class ProviderAPIError(Exception):
    pass


class APIAuthException(ProviderAPIError):
    pass


# Highly I/O bound task, recommended to be consumed by several workers
@celery.shared_task(bind=True, ignore_result=True)
def create_submission(
    task, submission_key, course_key, submission_api_url, matching_start_time=''
):
    """
    Fetch submission data for a new submission with provider key submission_key from a given API url,
    create new submission, and tokenize submission content. If matching_start_time timestamp is given,
    it will be written into the submission object before writing.
    """
    course = Course.objects.get(key=course_key)
    if submission_exists(submission_key):
        write_error(
            "Submission with key %s already exists, will not create a duplicate."
            % submission_key,
            "create_submission",
        )
        return

    # We need someone with a token to the A+ API.
    api_client = aplus.get_api_client(course)
    # Request data from provider API
    try:
        data = api_client.load_data(submission_api_url)
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.ReadTimeout,
    ):
        logger.exception("Unable to read data from the API.")
        data = None

    del api_client

    if not data:
        logger.error(
            "API returned nothing for submission %s, skipping submission",
            submission_key,
        )
        return

    exercise_data = data["exercise"]

    # Check if exercise is configured for Radar
    # If not, and there is no manually configured exercise in the database, skip
    radar_config = aplus.get_radar_config(exercise_data, course)
    if radar_config is None and not course.has_exercise(str(exercise_data["id"])):
        return

    # Get or create exercise configuration
    exercise = course.get_exercise(str(exercise_data["id"]))
    if exercise.name == "unknown":
        # Get template source
        try:
            radar_config["template_source"] = radar_config["get_template_source"]()
        except Exception as e:
            write_error(
                "Error while attempting to get template source for submission %s\n%s"
                % (submission_key, str(e)),
                "create_submission",
            )
            radar_config["template_source"] = ''
        exercise.set_from_config(radar_config)
        exercise.save()

    del radar_config

    # A+ allows more than one submitter for a single submission
    # TODO: if there are more than one unique submitters,
    # set as approved plagiate and show this in the UI
    ## for submitter_id in _decode_students(data["submitters"]):
    submitter_id = "_".join(aplus._decode_students(data["submitters"]))

    # Check if any of the submitters is a staff member
    is_staff = check_if_staff(data, course)

    if is_staff:
        submitter_id += "_STAFF"

    try:
        submission = insert_submission(exercise, submission_key, submitter_id, data)

        # If any of the submitters is a staff member, set the student as staff
        if is_staff:
            staff = submission.student
            staff.is_staff = True
            staff.save()

        prepare_submission(submission, matching_start_time)
    except InsertError as err:
        write_error(str(err), 'create_submission')
        return


@celery.shared_task(ignore_result=True)
def reload_exercise_submissions(exercise_id, submissions_api_url):
    """
    Fetch the current submission list from the API url, clear existing submissions, create new submissions,
    and match all submissions.
    """
    exercise = Exercise.objects.get(pk=exercise_id)
    api_client = aplus.get_api_client(exercise.course)
    submissions_data = api_client.load_data(submissions_api_url)
    if submissions_data is None:
        # raise ProviderTaskError("Invalid submissions data returned from %s for exercise %s:
        # expected an iterable but got None" % (submissions_api_url, exercise))
        write_error(
            "Invalid submissions data returned from %s for exercise %s: expected an iterable but got None"
            % (submissions_api_url, exercise),
            "reload_exercise_submissions",
        )
        return
    # We got new submissions data from the provider, delete all current submissions to this exercise
    exercise.submissions.all().delete()
    # Overwrite timestamp for new matching task
    exercise.touch_all_timestamps()
    # Create every submission and set timestamp
    for submission in submissions_data:
        create_submission(
            submission["id"],
            exercise.course.key,
            submission["url"],
            exercise.matching_start_time,
        )
    # All submissions created, now match them
    if not DEBUG or CELERY_DEBUG:
        matcher_tasks.match_all_new_submissions_to_exercise.delay(exercise_id)


@celery.shared_task
def get_full_course_config(api_user_id, course_id, has_radar_config=True):
    """
    Perform full traversal of the exercises list of a course in the A+ API.
    The API access token of a RadarUser with the given id will be used for access.
    If has_radar_config is given and False, all submittable exercises will be retireved.
    Else, only exercises defined with Radar configuration data will be retrieved.
    """
    result = {}
    course = Course.objects.get(pk=course_id)
    client = aplus.get_api_client(course.namespace)

    try:
        if client is None:
            raise APIAuthException
        response = client.load_data(course.url)
        if response is None:
            raise APIAuthException
        exercises = response.get("exercises", [])
    except APIAuthException:
        exercises = []
        result.setdefault("errors", []).append(
            "This user does not have correct credentials to use the API of %s"
            % repr(course)
        )

    if not exercises:
        result.setdefault("errors", []).append(
            "No exercises found for %s" % repr(course)
        )

    if has_radar_config:
        # Exercise API data is expected to contain Radar configurations
        # Partition all radar configs into unseen and existing exercises
        new_exercises, old_exercises = [], []
        for radar_config in aplus.leafs_with_radar_config(exercises, course):
            radar_config["template_source"] = radar_config["get_template_source"]()
            # We got the template and lambdas are not serializable so we delete the getter
            del radar_config["get_template_source"]
            if course.has_exercise(radar_config["exercise_key"]):
                old_exercises.append(radar_config)
            else:
                new_exercises.append(radar_config)
        result["exercises"] = {
            "old": old_exercises,
            "new": new_exercises,
            "new_json": json.dumps(new_exercises),
        }
    else:
        # Exercise API data is not expected to contain Radar data,
        # choose all submittable exercises and patch them with a default Radar config
        new_exercises = []
        # Note that the type of 'exercise' is AplusApiDict
        for exercise in aplus.submittable_exercises(exercises):
            # Avoid overwriting exercise_info if it is defined
            patched_exercise_info = dict(
                exercise["exercise_info"] or {},
                radar={"tokenizer": "skip", "minimum_match_tokens": 15},
            )
            exercise.add_data({"exercise_info": patched_exercise_info})
            radar_config = aplus.get_radar_config(exercise, course)
            if radar_config:
                radar_config["template_source"] = radar_config["get_template_source"]()
                del radar_config["get_template_source"]
                new_exercises.append(radar_config)
        result["exercises"] = {
            "new": new_exercises,
            "tokenizer_choices": settings.TOKENIZER_CHOICES,
        }

    return result


@celery.shared_task(ignore_result=True)
def recompare_all_unmatched(course_id):
    course = Course.objects.get(pk=course_id)
    p_config = config_loaders.provider_config(course.provider)
    recompare = config_loaders.configured_function(p_config, "recompare")
    for exercise in course.exercises_with_unmatched_submissions:
        recompare(exercise, p_config)


@celery.shared_task(ignore_result=True)
def task_error_handler(task_id, *args, **kwargs):
    write_error("Failed celery task {}".format(task_id), "task_error_handler")


def write_error(message, namespace):
    logger.error(message)
    TaskError(package="provider", namespace=namespace, error_string=message).save()


# Check if any of the submitters is a staff member
def check_if_staff(data, course):
    is_staff = False

    # Check if any group submission submitters are staff
    for submitter in data["submitters"]:
        # Get the user data from the API
        try:
            api_client = aplus.get_api_client(course)
            submitter_data = api_client.load_data(submitter["url"])
            del api_client
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):
            logger.exception("Unable to read data from the API.")
            continue

        # Check if the user is a staff member for this course
        for course_data in submitter_data["staff_courses"]:
            if course_data["id"] == course.api_id:
                is_staff = True
                break

        if is_staff:
            break

    return is_staff
