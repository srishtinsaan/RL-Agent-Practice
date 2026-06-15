from prometheus_client import start_http_server, Gauge
import subprocess
import time

fdb_age = Gauge(
    "ovs_fdb_entry_age",
    "FDB entry age",
    ["port", "vlan", "mac"]
)


def update():
    output = subprocess.check_output(
        ["ovs-appctl", "fdb/show", "g0_s1"],
        text=True
    )

    fdb_age.clear()

    for line in output.splitlines():
        parts = line.split()

        if len(parts) < 4:
            continue

        # Skip header row
        if parts[3].lower() == "age":
            continue

        port = parts[0]
        vlan = parts[1]
        mac = parts[2]

        try:
            age = float(parts[3])
        except ValueError:
            print(f"Skipping invalid line: {line}")
            continue

        fdb_age.labels(
            port=port,
            vlan=vlan,
            mac=mac
        ).set(age)

start_http_server(8000)
print("FDB Exporter Running on :8000")
running = True
try:
    while running:
        update()
        time.sleep(1)

except KeyboardInterrupt:
    running = False
    print("Exporter Deactivated")