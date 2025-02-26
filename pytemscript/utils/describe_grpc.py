import subprocess
import argparse
from typing import Optional, List


PORT = 46699
SERVICES = [
    "utapi.optics.v1.OpticsService",
    "utapi.acquisition.v1.AcquisitionService",
]


def describe_service(server, service):
    # Describe the service to get methods
    command = ["grpcurl", "-plaintext",
               server + ":%d" % PORT,
               "describe", service]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("Error describing service: {}".format(stderr.decode('utf-8')))
        return []
    return stdout.decode('utf-8').splitlines()


def describe_message(server, message_type):
    # Describe the message type
    command = ["grpcurl", "-plaintext",
               server + ":%d" % PORT,
               "describe", message_type]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("Error describing message type: {}".format(stderr.decode('utf-8')))
        return ""
    return stdout.decode('utf-8')


def generate_proto(server, services):
    proto_content = "syntax = \"proto3\";\n\n"

    for service in services:
        proto_content += "// Service: {}\n".format(service)
        proto_content += "service {}".format(service.split('.')[-1])
        proto_content += " {\n"

        methods = describe_service(server, service)

        for line in methods:
            if line.strip().startswith("rpc"):
                proto_content += "{}\n".format(line)

        proto_content += "}\n\n"

        # Describe methods to get input and output types
        for line in methods:
            if line.strip().startswith("rpc"):
                input_type = line.split('(')[1].split(')')[0].strip()
                output_type = line.split("returns")[1].split()[1].strip()

                proto_content += "// Input message: {}\n".format(input_type)
                proto_content += describe_message(server, input_type)
                proto_content += "\n"

                proto_content += "// Output message: {}\n".format(output_type)
                proto_content += describe_message(server, output_type)
                proto_content += "\n"

    return proto_content


def main(argv: Optional[List] = None) -> None:
    parser = argparse.ArgumentParser(
        description="This script connects to the UTAPI server and creates "
                    "a .proto file with interface description",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", type=str,
                        default='192.168.76.2',
                        help="Microscope IP address")
    args = parser.parse_args(argv)

    proto_file_content = generate_proto(args.host, SERVICES)

    with open("%s.proto" % args.host, "w") as proto_file:
        proto_file.write(proto_file_content)

    print("Proto file generated: %s.proto" % args.host)


if __name__ == "__main__":
    main()
