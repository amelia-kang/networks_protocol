import tkinter as tk
from socket import socket, AF_INET, SOCK_STREAM
import sys

def connect(client, request, request_code, is_connected):
    try:
        if len(request) == 1:
            server_info = input(
                'Example: localhost 9090\nEnter server IP and port separated by space: ').split()
            if len(server_info)<2:
                print('Insufficient server information given. Please try again. Example: localhost 9090')
                return None, False, None
        else:
            server_info = request[1:]
        host = server_info[0]
        port = server_info[1]
        if port.isdigit():
            client.connect((host, int(port)))
        else:
            print('Incorrect port given. Port must be a number e.g. 9090. Please try again.')
            return None, False, None
    except Exception as e:
        raise Exception('Connection cannot be established.\nException: {}'.format(e))
    is_connected = True
    client.send(request_code.encode())
    print('Request {} sent to server, waiting for response...'.format(request))
    response = client.recv(1024)
    print('Server response:\n', response.decode())
    return client, is_connected, request

def disconnect(client, request, request_code, is_connected):
    client.send(request_code.encode())
    client.close()
    is_connected = False
    print('Connection closed.')
    return client, is_connected
        
def post(request, request_code):
    # If length of request is 1, hint user to keep inputting
    if len(request) == 1:
        request_content = input('Request requires: coordinates, width, height, color, "message" and status, separated by space.\
                \nExample: 6 6 5 5 red Pick up Fred from home at 5 pinned. Note that negative values will be converted to positive.\
                \nEnter your POST message: ')
        if request_content == '':
            print('No input provided. Please retry.')
            return None
        request_split = request_content.split()
        request = request[0] + ' ' + request_content
    else:
        request_split = request[1:]
        request = request_raw
        if len(request_split) < 5:
            print('Insufficient params in the request. Please try again.')
            return None
    # Validate if first 4 inputs are numbers
    if not request_split[0].isdigit() or not request_split[1].isdigit() or not request_split[2].isdigit() or not request_split[3].isdigit():
        print('Invalid request input: the first 4 inputs must be numbers. Please try again.')
        return None
    if int(request_split[2])==0 or int(request_split[3])==0:
        print('Width and height of the note must be greater than 0! Please try again.')
        return None
    return request


def get(request, request_code, request_raw):
    if len(request)==1:
        get_param = input(
            'Example 1 - color=red contains=4,6 refersTo=Fred, each separated by space\
                \nExample 2 - PINS or ALL\
                \nYour GET param: ')
        if get_param == '':
            print('No input provided. Please retry.')
            return None
        request = request_code + ' ' + get_param
    else:
        request = request_raw
    return request


def pin_unpin(request, request_code, request_raw):
    # If user enter PIN or UNPIN, show instructions
    if len(request)==1:
        coords = input('Example: 7,7\nEnter a pair of coordinate separated by comma: ')
        if ',' in coords:
            coords_list = coords.split(',') 
            request = request_code+' '+coords
        else:
            print('Invalid format of PIN/UNPIN parameter. Example: 6,7. Please try again.')
            return None
    # If usre enters PIN/UNPIN 6,7, proceed
    elif len(request)==2: 
        if ',' in request[1]:
            coords_list = request[1].split(',')
            request = request_raw
        else:
            print('Invalid format of PIN/UNPIN parameter. Example: PIN 6,7. Please try again.')
            return None
    else:
        print('Invalid format of this PIN/UNPIN request. Example: PIN 6,7. Please try again.')
        return None
    # Validate if the coordinates are numbers
    if len(coords_list) != 2 or not coords_list[0].isdigit() or not coords_list[1].isdigit():
        print('Invalid coordinates entered. Please retry and enter 2 digits.')
        return None 
    return request


if __name__ == "__main__":

    AVAIL_REQS = ['CONNECT', 'DISCONNECT', 'POST', 'GET', 'PIN', 'UNPIN', 'CLEAR']
    print('Available commands:', AVAIL_REQS)

    # Define TCP socket
    client = socket(AF_INET, SOCK_STREAM)
    is_connected = False

    while True:
        # Get capitalized user input
        request_raw = input('Input a request: ').strip()

        if request_raw == '':
            continue

        request = request_raw.split()
        request_code = request[0].upper()
        if request_code not in AVAIL_REQS:
            print('Given request is not valid. Please check valid options and retry.')
            continue
        try:
            if request_code == 'CONNECT':
                if is_connected == True:
                    print('Client already connected to a server {}'.format)
                    continue
                client, is_connected, request = connect(client, request, request_code, is_connected)
                if not client:
                    continue

            elif request_code == 'DISCONNECT':
                if is_connected == False:
                    print('Client has not opened a connection or connection already closed.')
                else:
                    client, is_connected = disconnect(client, request, request_code, is_connected)
                break
            else:
                if is_connected == False:
                    print('No open connection established. Please CONNECT to server first.')
                    continue
                if request_code == 'POST':
                    request = post(request, request_code)
                    if request == None:
                        continue  
                elif request_code == 'GET':
                    request = get(request, request_code, request_raw)
                    if not request:
                        continue
                elif request_code == 'PIN' or request_code=='UNPIN':
                    request = pin_unpin(request, request_code, request_raw)
                    if not request:
                        continue
                elif request_code == 'CLEAR':
                    request = request_code

                # Send request message to server
                client.send(request.encode())
                print('Request {} sent to server, waiting for response...'.format(request))
                # Collect server response
                response = client.recv(1024)
                print('Server response:\n{}'.format(response.decode()))

        except Exception as e:
            print('Exception occurred: {}\nPlease follow instructions and try again.'.format(e))
            continue
