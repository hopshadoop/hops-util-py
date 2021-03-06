"""
Utility functions to export models to the Models dataset and get information about models currently being served
in the project.
"""

from hops import hdfs, constants, util, exceptions, kafka
import json
import re


def exists(serving_name):
    """
    Checks if there exists a serving with the given name

    Example use-case:

    >>> from hops import serving
    >>> serving.exist(serving_name)

    Args:
        :serving_name: the name of the serving

    Returns:
           True if the serving exists, otherwise false
    """
    try:
        return get_id(serving_name) is not None
    except ServingNotFound as e:
        print("No serving with name {} was found in the project {}".format(serving_name, hdfs.project_name()))
        return False


def delete(serving_name):
    """
    Deletes serving instance with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.delete("irisFlowerClassifier")

    Args:
        :serving_name: name of the serving to delete

    Returns:
        None
    """
    serving_id = get_id(serving_name)
    print("Deleting serving with name: {}...".format(serving_name))
    _delete_serving_rest(serving_id)
    print("Serving with name: {} successfully deleted".format(serving_name))


def _delete_serving_rest(serving_id):
    """
    Makes a REST request to Hopsworks REST API for deleting a serving instance

    Args:
        :serving_id: id of the serving to delete

    Returns:
        None

    Raises:
        :RestAPIError: if there was an error with the REST call to Hopsworks
    """
    method = constants.HTTP_CONFIG.HTTP_DELETE
    resource_url = (constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_REST_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_PROJECT_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    hdfs.project_id() + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_SERVING_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER
                    + str(serving_id))
    response = util.send_request(method, resource_url)

    if response.status_code != 200:
        response_object = response.json()
        error_code, error_msg, user_msg = util._parse_rest_error(response_object)
        raise exceptions.RestAPIError("Could not delete serving with id {} (url: {}), "
                                      "server response: \n "
                                      "HTTP code: {}, HTTP reason: {}, error code: {}, error msg: {}, "
                                      "user msg: {}".format(serving_id, resource_url, response.status_code,
                                                            response.reason, error_code, error_msg, user_msg))


def start(serving_name):
    """
    Starts a model serving instance with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.start("irisFlowerClassifier")

    Args:
        :serving_name: name of the serving to start

    Returns:
        None
    """
    serving_id = get_id(serving_name)
    print("Starting serving with name: {}...".format(serving_name))
    _start_or_stop_serving_rest(serving_id, constants.MODEL_SERVING.SERVING_ACTION_START)
    print("Serving with name: {} successfully started".format(serving_name))


def stop(serving_name):
    """
    Stops a model serving instance with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.stop("irisFlowerClassifier")

    Args:
        :serving_name: name of the serving to stop

    Returns:
        None
    """
    serving_id = get_id(serving_name)
    print("Stopping serving with name: {}...".format(serving_name))
    _start_or_stop_serving_rest(serving_id, constants.MODEL_SERVING.SERVING_ACTION_STOP)
    print("Serving with name: {} successfully stopped".format(serving_name))


def _start_or_stop_serving_rest(serving_id, action):
    """
    Makes a REST request to Hopsworks REST API for starting/stopping a serving instance

    Args:
        :serving_id: id of the serving to start/stop
        :action: the action to perform (start or stop)

    Returns:
        None

    Raises:
        :RestAPIError: if there was an error with the REST call to Hopsworks
    """
    method = constants.HTTP_CONFIG.HTTP_POST
    resource_url = (constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_REST_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_PROJECT_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    hdfs.project_id() + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_SERVING_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER
                    + str(serving_id) + constants.MODEL_SERVING.SERVING_START_OR_STOP_PATH_PARAM + action)
    response = util.send_request(method, resource_url)

    if response.status_code != 200:
        response_object = response.json()
        error_code, error_msg, user_msg = util._parse_rest_error(response_object)
        raise exceptions.RestAPIError("Could not perform action {} on serving with id {} (url: {}), "
                                      "server response: \n "
                                      "HTTP code: {}, HTTP reason: {}, error code: {}, error msg: {}, "
                                      "user msg: {}".format(action, serving_id, resource_url, response.status_code,
                                                            response.reason, error_code, error_msg, user_msg))


def create_or_update(serving_name, artifact_path, model_version=1, model_server=None, kfserving=False,
                             batching_enabled = False, topic_name="CREATE",  num_partitions = 1, num_replicas = 1,
                             instances = 1):
    """
    Creates a serving in Hopsworks if it does not exist, otherwise update the existing one.
    In case model server is not specified, it is inferred from the artifact files.

    Example use-case:

    >>> from hops import serving
    >>> serving.create_or_update("mnist", "/Models/mnist", 1)

    Args:
        :serving_name: name of the serving to create
        :artifact_path: path to the artifact to serve (tf model dir or python script implementing the Predict class)
        :model_version: version of the model to serve
        :model_server: name of the model server to deploy, e.g "TENSORFLOW_SERVING" or "FLASK"
        :kfserving: boolean flag whether to serve the model using KFServing serving tool
        :batching_enabled: boolean flag whether to enable batching for the inference requests
        :instances: the number of serving instances (the more instances the more inference requests can
        be served in parallel)
        :kfserving: boolean flag whether to serve the model using KFServing

    Returns:
          None
    """
    serving_id = get_id(serving_name)
    artifact_path = hdfs._expand_path(artifact_path)
    if model_server is None:
        model_server = _detect_model_server(artifact_path)

    _validate_user_serving_input(serving_name, artifact_path, model_version, model_server, kfserving, batching_enabled,
                                 topic_name, num_partitions, num_replicas, instances)
    artifact_path = hdfs.get_plain_path(artifact_path)
    print("Creating serving {} for artifact {} ...".format(serving_name, artifact_path))
    _create_or_update_serving_rest(serving_name, artifact_path, model_version, model_server, kfserving, batching_enabled,
                                   topic_name, num_partitions, num_replicas, serving_id, instances)
    print("Serving {} successfully created".format(serving_name))


def _validate_user_serving_input(serving_name, model_path, model_version, model_server, kfserving, batching_enabled, topic_name,
                                 num_partitions, num_replicas, instances):
    """
    Validate user input on the client side before sending REST call to Hopsworks (additional validation will be done
    in the backend)

    Args:
        :serving_name: the name of the serving to create
        :model_path: path to the model or artifact being served
        :model_version: version of the serving
        :model_server: name of the model server to deploy, e.g "TENSORFLOW_SERVING" or "FLASK"
        :kfserving: boolean flag whether to serve the model using KFServing serving tool
        :batching_enabled: boolean flag whether to enable batching for inference requests to the serving
        :num_partitions: kafka partitions
        :num_replicas: kafka replicas
        :instances: the number of serving instances (the more instances the more inference requests can
                    be served in parallel)

    Returns:
        None

    Raises:
        :ValueError: if the serving input failed the validation
    """
    name_pattern = re.compile("^[a-zA-Z0-9]+$")
    if len(serving_name) > 256 or serving_name == "" or not name_pattern.match(serving_name):
        raise ValueError("Name of serving cannot be empty, cannot exceed 256 characters and must match the regular "
                         "expression: ^[a-zA-Z0-9]+$, the provided name: {} is not valid".format(serving_name))
    if not hdfs.exists(model_path):
        raise ValueError("The model/artifact path must exist in HDFS, the provided path: {} "
                         "does not exist".format(model_path))
    if model_server not in constants.MODEL_SERVING.MODEL_SERVERS:
        raise ValueError("The provided model_server: {} is not supported, supported "
                         "model servers are: {}".format(model_server, ",".join(constants.MODEL_SERVING.MODEL_SERVERS)))
    if not isinstance(model_version, int):
        raise ValueError("The model version must be an integer, the provided version is not: {}".format(model_version))
    if model_server == constants.MODEL_SERVING.MODEL_SERVER_TENSORFLOW_SERVING:
        if not isinstance(num_replicas, int):
            raise ValueError("Number of kafka topic replicas must be an integer, the provided num replicas "
                             "is not: {}".format(model_version))
        if not isinstance(num_partitions, int):
            raise ValueError("Number of kafka topic partitions must be an integer, the provided num partitions "
                             "is not: {}".format(num_partitions))
        if not isinstance(batching_enabled, bool):
            raise ValueError("Batching enabled must be a boolean, the provided value "
                             "is not: {}".format(batching_enabled))
        if kfserving and batching_enabled:
            raise ValueError("Batching requests is currently not supported in KFServing deployments")

    if kfserving and model_server == constants.MODEL_SERVING.MODEL_SERVER_FLASK:
        raise ValueError("Flask is currently not supported for KFServing deployments")
    if not isinstance(instances, int):
        raise ValueError("The number of serving instances must be an integer, "
                         "the provided version is not: {}".format(instances))


def _create_or_update_serving_rest(serving_name, model_path, model_version, model_server, kfserving,
                                   batching_enabled=None, topic_name=None, num_partitions=None,
                                   num_replicas=None, serving_id=None, instances=1):
    """
    Makes a REST request to Hopsworks for creating or updating a model serving instance

    Args:
        :serving_name: the name of the serving to create
        :model_path: path to the model or artifact being served
        :model_version: version of the serving
        :model_server: name of the model server to deploy, e.g "TENSORFLOW_SERVING" or "FLASK"
        :kfserving: boolean flag whether to serve the model using KFServing serving tool
        :batching_enabled: boolean flag whether to enable batching for inference requests to the serving
        :topic_name: name of the kafka topic ("CREATE" to create a new one, or "NONE" to not use kafka topic)
        :num_partitions: kafka partitions
        :num_replicas: kafka replicas
        :serving_id: the id of the serving in case of UPDATE, if serving_id is None, it is a CREATE operation.
        :instances: the number of serving instances (the more instances the more inference requests can
        be served in parallel)
        :kfserving: boolean flag whether to serve the model using KFServing

    Returns:
        None

    Raises:
        :RestAPIError: if there was an error with the REST call to Hopsworks
    """

    serving_tool = constants.MODEL_SERVING.SERVING_TOOL_KFSERVING if kfserving else constants.MODEL_SERVING.SERVING_TOOL_DEFAULT

    json_contents = {
        constants.REST_CONFIG.JSON_SERVING_MODEL_VERSION: model_version,
        constants.REST_CONFIG.JSON_SERVING_ARTIFACT_PATH: model_path,
        constants.REST_CONFIG.JSON_MODEL_SERVER: model_server,
        constants.REST_CONFIG.JSON_SERVING_TOOL: serving_tool,
        constants.REST_CONFIG.JSON_SERVING_NAME: serving_name,
        constants.REST_CONFIG.JSON_SERVING_KAFKA_TOPIC_DTO: {
            constants.REST_CONFIG.JSON_KAFKA_TOPIC_NAME: topic_name,
            constants.REST_CONFIG.JSON_KAFKA_NUM_PARTITIONS: num_partitions,
            constants.REST_CONFIG.JSON_KAFKA_NUM_REPLICAS: num_replicas
        },
        constants.REST_CONFIG.JSON_SERVING_REQUESTED_INSTANCES: instances,
    }
    if serving_id is not None:
        json_contents[constants.REST_CONFIG.JSON_SERVING_ID] = serving_id
    if model_server == constants.MODEL_SERVING.MODEL_SERVER_TENSORFLOW_SERVING:
        json_contents[constants.REST_CONFIG.JSON_SERVING_BATCHING_ENABLED] = batching_enabled
    json_embeddable = json.dumps(json_contents)
    headers = {constants.HTTP_CONFIG.HTTP_CONTENT_TYPE: constants.HTTP_CONFIG.HTTP_APPLICATION_JSON}
    method = constants.HTTP_CONFIG.HTTP_PUT
    resource_url = (constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_REST_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_PROJECT_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    hdfs.project_id() + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_SERVING_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER)
    response = util.send_request(method, resource_url, data=json_embeddable, headers=headers)

    if response.status_code != 201 and response.status_code != 200:
        response_object = response.json()
        error_code, error_msg, user_msg = util._parse_rest_error(response_object)
        raise exceptions.RestAPIError("Could not create or update serving (url: {}), server response: \n " \
                                      "HTTP code: {}, HTTP reason: {}, error code: {}, error msg: {}, "
                                      "user msg: {}".format(resource_url, response.status_code, response.reason,
                                                            error_code, error_msg, user_msg))


def _detect_model_server(artifact_path):
    model_server = constants.MODEL_SERVING.MODEL_SERVER_TENSORFLOW_SERVING
    if artifact_path.endswith(".py"):
        model_server = constants.MODEL_SERVING.MODEL_SERVER_FLASK
    print("Inferring model server from artifact files: {}".format(model_server))
    return model_server


def get_id(serving_name):
    """
    Gets the id of a serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_id(serving_name)

    Args:
        :serving_name: name of the serving to get the id for

    Returns:
         the id of the serving, None if Serving does not exist
    """
    try:
        servings = get_all()
        serving = _find_serving_with_name(serving_name, servings)
        return serving.id
    except ServingNotFound:
        return None


def get_artifact_path(serving_name):
    """
    Gets the artifact path of a serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_artifact_path(serving_name)

    Args:
        :serving_name: name of the serving to get the artifact path for

    Returns:
         the artifact path of the serving (model path in case of tensorflow, or python script in case of SkLearn)
    """
    servings = get_all()
    serving = _find_serving_with_name(serving_name, servings)
    return serving.artifact_path


def get_model_server(serving_name):
    """
    Gets the type of model server of the serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_model_server(serving_name)

    Args:
        :serving_name: name of the serving to get the type for

    Returns:
         the model server (e.g Tensorflow Serving or Flask)
    """
    servings = get_all()
    serving = _find_serving_with_name(serving_name, servings)
    return serving.model_server


def get_serving_tool(serving_name):
    """
    Gets the serving tool of the serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_serving_tool(serving_name)

    Args:
        :serving_name: name of the serving to get the mode for

    Returns:
         the serving tool (e.g DEFAULT or KFSERVING)
    """
    servings = get_all()
    serving = _find_serving_with_name(serving_name, servings)
    return serving.serving_tool


def get_version(serving_name):
    """
    Gets the version of a serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_version(serving_name)

    Args:
        :serving_name: name of the serving to get the version for

    Returns:
         the version of the serving
    """
    servings = get_all()
    serving = _find_serving_with_name(serving_name, servings)
    return serving.model_version


def get_kafka_topic(serving_name):
    """
    Gets the kafka topic name of a serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_kafka_topic(serving_name)

    Args:
        :serving_name: name of the serving to get the kafka topic name for

    Returns:
         the kafka topic name of the serving
    """
    servings = get_all()
    serving = _find_serving_with_name(serving_name, servings)
    return serving.kafka_topic_dto.name


def get_status(serving_name):
    """
    Gets the status of a serving with a given name

    Example use-case:

    >>> from hops import serving
    >>> serving.get_status(serving_name)

    Args:
        :serving_name: name of the serving to get the status for

    Returns:
         the status of the serving
    """
    servings = get_all()
    serving = _find_serving_with_name(serving_name, servings)
    return serving.status


def get_all():
    """
    Gets the list of servings for the current project

    Example:

    >>> from hops import serving
    >>> servings = serving.get_all()
    >>> servings[0].name

    Returns:
         list of servings
    """
    return _parse_json_servings(_get_servings_rest())


def _find_serving_with_name(serving_name, servings):
    """
    Finds a serving with a given name from a list of servings (O(N))

    Args:
        :serving_name: name of the serving to look for
        :servings: the list of servings to look through

    Returns:
           serving with the given name

    Raises:
        :ServingNotFound: if the requested serving could not be found
    """
    serving_names = []
    for serving in servings:
        if serving.name == serving_name:
            return serving
        serving_names.append(serving.name)
    serving_names_str = ",".join(serving_names)
    raise ServingNotFound("No serving with name: {} could be found among the list of "
                          "available servings: {}".format(serving_name, serving_names_str))


def _parse_json_servings(json_servings):
    """
    Parses a list of JSON servings into Serving Objects

    Args:
        :json_servings: the list of JSON servings

    Returns:
           a list of Serving Objects
    """
    return list(map(lambda json_serving: Serving(json_serving), json_servings))


def _get_servings_rest():
    """
    Makes a REST request to Hopsworks to get a list of all servings in the current project

    Returns:
         JSON response parsed as a python dict

    Raises:
        :RestAPIError: if there was an error with the REST call to Hopsworks
    """
    method = constants.HTTP_CONFIG.HTTP_GET
    resource_url = (constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_REST_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_PROJECT_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    hdfs.project_id() + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_SERVING_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER)
    response = util.send_request(method, resource_url)
    response_object = response.json()
    if response.status_code != 200:
        error_code, error_msg, user_msg = util._parse_rest_error(response_object)
        raise exceptions.RestAPIError("Could not fetch list of servings from Hopsworks REST API (url: {}), "
                                      "server response: \n "
                                      "HTTP code: {}, HTTP reason: {}, error code: {}, "
                                      "error msg: {}, user msg: {}".format(
            resource_url, response.status_code, response.reason, error_code, error_msg, user_msg))
    return response_object


def make_inference_request(serving_name, data, verb=":predict"):
    """
    Submit an inference request

    Example use-case:

    >>> from hops import serving
    >>> serving.make_inference_request("irisFlowerClassifier", [[1,2,3,4]], ":predict")

    Args:
        :serving_name: name of the model being served
        :data: data/json to send to the serving
        :verb: type of request (:predict, :classify, or :regress)

    Returns:
        the JSON response
    """
    return _make_inference_request_rest(serving_name, data, verb)

def _make_inference_request_rest(serving_name, data, verb):
    """
    Makes a REST request to Hopsworks for submitting an inference request to the serving instance

    Args:
        :serving_name: name of the model being served
        :data: data/json to send to the serving
        :verb: type of request (:predict, :classify, or :regress)

    Returns:
        the JSON response

    Raises:
        :RestAPIError: if there was an error with the REST call to Hopsworks
    """
    json_embeddable = json.dumps(data)
    headers = {constants.HTTP_CONFIG.HTTP_CONTENT_TYPE: constants.HTTP_CONFIG.HTTP_APPLICATION_JSON}
    method = constants.HTTP_CONFIG.HTTP_POST
    resource_url = (constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_REST_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_PROJECT_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    hdfs.project_id() + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_INFERENCE_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER +
                    constants.REST_CONFIG.HOPSWORKS_MODELS_RESOURCE + constants.DELIMITERS.SLASH_DELIMITER
                    + serving_name + verb)
    response = util.send_request(method, resource_url, data=json_embeddable, headers=headers)
    response_object = response.json()
    error_code, error_msg, user_msg = util._parse_rest_error(response_object)

    if response.status_code != 201 and response.status_code != 200:
        raise exceptions.RestAPIError("Could not create or update serving (url: {}), server response: \n " \
                                      "HTTP code: {}, HTTP reason: {}, error code: {}, error msg: {}, "
                                      "user msg: {}".format(resource_url, response.status_code, response.reason,
                                                            error_code, error_msg, user_msg))
    return response_object

class Serving(object):
    """
    Represents a model being served in Hopsworks
    """

    def __init__(self, serving_json):
        """
        Initialize the serving from JSON payload returned by Hopsworks REST API

        Args:
            :feature_json: JSON data about the feature returned from Hopsworks REST API
        """
        self.status = serving_json[constants.REST_CONFIG.JSON_SERVING_STATUS]
        self.artifact_path = serving_json[constants.REST_CONFIG.JSON_SERVING_ARTIFACT_PATH]
        self.name = serving_json[constants.REST_CONFIG.JSON_SERVING_NAME]
        self.creator = serving_json[constants.REST_CONFIG.JSON_SERVING_CREATOR]
        self.creator = serving_json[constants.REST_CONFIG.JSON_SERVING_CREATOR]
        self.model_server = serving_json[constants.REST_CONFIG.JSON_MODEL_SERVER]
        self.serving_tool = serving_json[constants.REST_CONFIG.JSON_SERVING_TOOL]
        self.model_version = serving_json[constants.REST_CONFIG.JSON_SERVING_MODEL_VERSION]
        self.created = serving_json[constants.REST_CONFIG.JSON_SERVING_CREATED]
        self.requested_instances = serving_json[constants.REST_CONFIG.JSON_SERVING_REQUESTED_INSTANCES]
        if constants.REST_CONFIG.JSON_SERVING_KAFKA_TOPIC_DTO in serving_json:
            self.kafka_topic_dto = kafka.KafkaTopicDTO(serving_json[constants.REST_CONFIG.JSON_SERVING_KAFKA_TOPIC_DTO])
        self.id = serving_json[constants.REST_CONFIG.JSON_SERVING_ID]


class ServingNotFound(Exception):
    """This exception will be raised if the requested serving could not be found"""
