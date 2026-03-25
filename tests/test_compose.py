import pathlib
import pytest
import yaml


@pytest.fixture(scope="module")
def compose():
    repo_root = pathlib.Path(__file__).parent.parent
    compose_path = repo_root / "docker-compose.yml"
    with compose_path.open() as f:
        return yaml.safe_load(f)


# Property 1: All services are declared with correct ports
# Validates: Requirements 1.1, 2.1, 3.1, 5.1
def test_services_and_ports(compose):
    """Feature: green-pulse-telemetry, Property 1: All services are declared with correct ports"""
    services = compose["services"]

    assert "mosquitto" in services, "mosquitto service must be declared"
    assert "influxdb" in services, "influxdb service must be declared"
    assert "grafana" in services, "grafana service must be declared"

    expected_ports = {
        "mosquitto": "1883",
        "influxdb": "8086",
        "grafana": "3000",
    }

    for service_name, expected_port in expected_ports.items():
        port_mappings = services[service_name]["ports"]
        host_ports = [str(p).split(":")[0] for p in port_mappings]
        assert expected_port in host_ports, (
            f"{service_name} must expose host port {expected_port}, got {host_ports}"
        )


# Property 2: All service images are pinned to specific versions
# Validates: Requirements 5.3
def test_pinned_image_versions(compose):
    """Feature: green-pulse-telemetry, Property 2: All service images are pinned to specific versions"""
    services = compose["services"]

    for service_name, service_def in services.items():
        image = service_def.get("image", "")
        assert image, f"{service_name} must have an image defined"
        assert ":" in image, f"{service_name} image must have an explicit tag: {image}"
        tag = image.split(":")[-1]
        assert tag != "latest", f"{service_name} image must not use 'latest' tag: {image}"
        assert tag != "", f"{service_name} image tag must not be empty: {image}"


# Property 3: Named volumes are declared and mounted for every service
# Validates: Requirements 1.3, 2.5, 3.3, 4.1, 4.3
def test_named_volumes_no_bind_mounts(compose):
    """Feature: green-pulse-telemetry, Property 3: Named volumes are declared and mounted for every service"""
    services = compose["services"]
    top_level_volumes = set(compose.get("volumes", {}).keys())

    for service_name, service_def in services.items():
        volume_mounts = service_def.get("volumes", [])
        assert volume_mounts, f"{service_name} must have at least one volume mount"

        named_mounts = []
        for mount in volume_mounts:
            mount_str = str(mount)
            source = mount_str.split(":")[0]
            # Bind mounts start with ./ or /
            assert not source.startswith("./") or "config" in mount_str, (
                f"{service_name} must not use bind mounts for persistence: {mount_str}"
            )
            if not source.startswith("./") and not source.startswith("/"):
                named_mounts.append(source)
                assert source in top_level_volumes, (
                    f"Volume '{source}' used in {service_name} must be declared in top-level volumes"
                )

        assert named_mounts, f"{service_name} must have at least one named volume mount"


# Property 4: InfluxDB initialization environment variables are all present and non-empty
# Validates: Requirements 2.2, 2.3, 2.4
def test_influxdb_env_vars_present_and_non_empty(compose):
    """Feature: green-pulse-telemetry, Property 4: InfluxDB initialization environment variables are all present and non-empty"""
    influxdb = compose["services"]["influxdb"]
    env = influxdb.get("environment", {})

    required_vars = [
        "DOCKER_INFLUXDB_INIT_MODE",
        "DOCKER_INFLUXDB_INIT_ORG",
        "DOCKER_INFLUXDB_INIT_BUCKET",
        "DOCKER_INFLUXDB_INIT_ADMIN_TOKEN",
        "DOCKER_INFLUXDB_INIT_USERNAME",
    ]

    for var in required_vars:
        assert var in env, f"InfluxDB env var {var} must be defined"
        assert str(env[var]).strip() != "", f"InfluxDB env var {var} must not be empty"


# Property 5: InfluxDB org and bucket values match specification
# Validates: Requirements 2.2, 2.3
def test_influxdb_org_and_bucket_values(compose):
    """Feature: green-pulse-telemetry, Property 5: InfluxDB org and bucket values match specification"""
    influxdb = compose["services"]["influxdb"]
    env = influxdb.get("environment", {})

    assert env.get("DOCKER_INFLUXDB_INIT_ORG") == "GreenPulse", (
        f"DOCKER_INFLUXDB_INIT_ORG must equal 'GreenPulse', got: {env.get('DOCKER_INFLUXDB_INIT_ORG')}"
    )
    assert env.get("DOCKER_INFLUXDB_INIT_BUCKET") == "telemetry", (
        f"DOCKER_INFLUXDB_INIT_BUCKET must equal 'telemetry', got: {env.get('DOCKER_INFLUXDB_INIT_BUCKET')}"
    )
