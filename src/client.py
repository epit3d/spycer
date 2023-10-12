import src.server_api.pyapi.srv_bug.srv_bug_pb2 as srv_bug_pb2
import src.server_api.pyapi.srv_bug.srv_bug_pb2_grpc as srv_bug_pb2_grpc
import grpc
import os
import yaml

CHUNK_SIZE = 1024 * 1024  # 1MB

def get_file_chunks(filename):
    with open(filename, 'rb') as f:
        while True:
            piece = f.read(CHUNK_SIZE);
            if len(piece) == 0:
                return
            yield piece

def prepare_bug(filename, error_description):
    with open("auth.yaml", 'r') as file:
        auth_data = yaml.safe_load(file)

    req = srv_bug_pb2.AddBugRequest(
        info=srv_bug_pb2.BugInfo(
            message=error_description,
            creds=srv_bug_pb2.Credentials(
                login=auth_data.get('login'),
                passw=auth_data.get('password')),
        )
    )
    yield req

    for piece in get_file_chunks(filename):
        yield srv_bug_pb2.AddBugRequest(content=piece)

def send_bug_report(filename, error_description):
    with grpc.insecure_channel("app.epit3d.com:3456") as channel:
        stub = srv_bug_pb2_grpc.BugServiceStub(channel)

        # check if file exists
        if not os.path.exists(filename):
            print("File not found: %s" % filename)
            return False

        msgs = prepare_bug(filename, error_description)

        print("prepared to call rpc")
        response = stub.AddBug(msgs)
        print(response)
        return True
