"""
Utility functions to retrieve information about available services and setting up security for the Hops platform.

These utils facilitates development by hiding complexity for programs interacting with Hops services.
"""

class ENV_VARIABLES:
    """
    Environment variable names (accessible in os.environ)
    """
    KAFKA_BROKERS_ENV_VAR = "KAFKA_BROKERS"
    ELASTIC_ENDPOINT_ENV_VAR = "ELASTIC_ENDPOINT"
    PWD_ENV_VAR = "PWD"
    KAFKA_VERSION_ENV_VAR = "KAFKA_VERSION"
    LIVY_VERSION_ENV_VAR = "LIVY_VERSION"
    SPARK_VERSION_ENV_VAR = "SPARK_VERSION"
    CUDA_VERSION_ENV_VAR = "SPARK_VERSION"
    REST_ENDPOINT_END_VAR = "REST_ENDPOINT"
    TENSORFLOW_VERSION_END_VAR = "TENSORFLOW_VERSION"

class KAFKA_SSL_CONFIG:
    """
    Kafka SSL constant strings for configuration
    """
    SSL_TRUSTSTORE_LOCATION_CONFIG = "ssl.truststore.location"
    SSL_TRUSTSTORE_LOCATION_DOC = "The location of the trust store file. "
    SSL_TRUSTSTORE_PASSWORD_CONFIG = "ssl.truststore.password"
    SSL_TRUSTSTORE_PASSWORD_DOC = "The password for the trust store file. If a password is not set access to the truststore is still available, but integrity checking is disabled."
    SSL_KEYSTORE_LOCATION_CONFIG = "ssl.keystore.location"
    SSL_KEYSTORE_PASSWORD_CONFIG = "ssl.keystore.password"
    SSL_KEY_PASSWORD_CONFIG = "ssl.key.password"
    SECURITY_PROTOCOL_CONFIG = "security.protocol"

# General SSL config properties

class SSL_CONFIG:
    """
    General SSL configuration constants for Hops-TLS
    """
    K_CERTIFICATE_CONFIG = "k_certificate"
    T_CERTIFICATE_CONFIG = "t_certificate"
    PEM_CLIENT_CERTIFICATE_CONFIG = "client.pem"
    PEM_CLIENT_KEY_CONFIG = "client_key.pem"
    PEM_CLIENT_CA_CERTIFICATE_CONFIG = "client_ca.pem"
    PEM_SERVER_CERTIFICATE_CONFIG = "server.pem"
    PEM_SERVER_KEY_CONFIG = "server_key.pem"
    PEM_SERVER_CA_CERTIFICATE_CONFIG = "server_ca.pem"
    PEM_T_CERTIFICATE_CONFIG = "t_certificate.pem"
    DOMAIN_CA_TRUSTSTORE = "domain_ca_truststore"
    CRYPTO_MATERIAL_PASSWORD = "material_passwd"

class KAFKA_PRODUCER_CONFIG:
    """
    Constant strings for Kafka producers
    """
    BOOTSTRAP_SERVERS_CONFIG = "bootstrap.servers"
    KEY_SERIALIZER_CLASS_CONFIG = "key.serializer"
    VALUE_SERIALIZER_CLASS_CONFIG = "value.serializer"

class KAFKA_CONSUMER_CONFIG:
    """
    Constant strings for Kafka consumers
    """
    GROUP_ID_CONFIG = "group.id"
    ENABLE_AUTO_COMMIT_CONFIG = "enable.auto.commit"
    AUTO_COMMIT_INTERVAL_MS_CONFIG = "auto.commit.interval.ms"
    SESSION_TIMEOUT_MS_CONFIG = "session.timeout.ms"
    KEY_DESERIALIZER_CLASS_CONFIG = "key.deserializer"
    VALUE_DESERIALIZER_CLASS_CONFIG = "value.deserializer"
    AUTO_OFFSET_RESET_CONFIG = "auto.offset.reset"
    ENABLE_AUTO_COMMIT_CONFIG = "enable.auto.commit"
    KEY_DESERIALIZER_CLASS_CONFIG = "key.deserializer"
    VALUE_DESERIALIZER_CLASS_CONFIG = "value.deserializer"

class REST_CONFIG:
    """
    REST endpoints and JSON properties used for communicating with Hopsworks REST API
    """
    JSON_JOBSTATE = "running"
    JSON_JOBIDS = "jobIds"
    JSON_KEYSTOREPWD = "keyStorePwd"
    JSON_SCHEMA_CONTENTS = "contents"
    JSON_SCHEMA_TOPICNAME = "topicName"
    JSON_SCHEMA_VERSION = "version"
    JSON_KEYSTORE = "keyStore"
    PROJECT_STAGING_DIR = "Resources"
    PROJECT_ROOT_DIR = "Projects"
    HOPSWORKS_REST_RESOURCE = "hopsworks-api/api"
    HOPSWORKS_REST_APPSERVICE = "appservice"
