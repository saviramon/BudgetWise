import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5552")

socket.send_string("get_total_savings")
reply = socket.recv_string()

print(f"Total savings: {reply}")
