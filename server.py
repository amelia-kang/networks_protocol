from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, active_count
import sys  # In order to terminate the program
from time import sleep


# Form connect server response to send back to client
def server_connect():
    response = 'Available colors for notes: ' + \
            str(AVAIL_COLORS) + '\nBoard size: ' + \
            str((BOARD_WIDTH, BOARD_HEIGHT))
    return response


# Clear any unpinned notes, and form response message for client
# param: global notes
def server_clear(notes):
    init_len = len(notes)
    notes = list(filter(lambda n: n['is_pinned']==True, notes))
    response = "{} unpinned note(s) removed".format(init_len-len(notes))
    return response, notes


# PIN or UNPIN message depending on the request code, then form response
def server_pin_unpin(request, request_code):
    pin_count = 0
    response = ''
    if len(request)==2 and ',' in request[1]:
        coords = request[1].split(',')
        x,y = int(coords[0]), int(coords[1])
        # Loop through each note
        for note in notes:
            # Find maching coordinates
            if note['x']==x and note['y']==y:
                # If asked to PIN, pin
                if request_code == 'PIN':
                    if note['is_pinned'] == True:
                        response += 'Note at {},{} already pinned'.format(x,y)
                    else:
                        note['is_pinned'] = True
                        pin_count+=1
                # If asked to unpin, unpin
                else:
                    if note['is_pinned'] == False:
                        response += 'Note at {},{} already not pinned'.format(x,y)
                    else:
                        note['is_pinned'] = False
                        pin_count+=1
        response += '{} note(s) {}.'.format(pin_count, 'pinned' if request_code=='PIN' else 'unpinned')
        return response


# Add the post to note board, update notes list, and return a response and notes
def server_post(request, notes):
    response = ''
    try:
        x = int(request[1])
        y = int(request[2])
        width = int(request[3])
        height = int(request[4])
        if x<0 or y<0 or y>BOARD_HEIGHT or width > BOARD_WIDTH or height>BOARD_HEIGHT:
            raise Exception("Note does not fit on the board. Please resize/re-position to fit it in {}x{}.".format(BOARD_WIDTH, BOARD_HEIGHT))

        color = request[5]
        # If the value at index 5 is not in available color list, set it to None
        if color.upper() not in AVAIL_COLORS:
            color = None
        # If status is not pinned, set is_pinned to False
        status = request[-1].upper()
        is_pinned = True if status == 'PINNED' else False

        if color and is_pinned:
            message = ' '.join(request[6:-1])
        elif color and not is_pinned:
            message = ' '.join(request[6:])
        elif is_pinned and not color:
            message = ' '.join(request[5:-1])
        else:
            message = ' '.join(request[5:])
        color = DEFAULT_COLOR if not color else color

        # Create note in dictionary
        note = {'x':x, 'y':y, 'width':width, 'height':height, 'color':color.upper(), 'message':message, 'is_pinned':is_pinned}
        print('note:',note)
        notes.append(note)
        response += 'Note added to the board successfully.'
    except Exception as e:
        response = e
    return response, notes


# Takes in request, GET required notes based on request params
def server_get(request, notes):
    response = ''
    # condition 0 GET ALL
    if request[1].upper() == 'ALL':
        response = "All notes:\n"
        for note in notes:
            response += '{},{} - {}\n'.format(note['x'],note['y'],note['message'])
    # condition 1 GET PINS
    elif request[1].upper() == 'PINS':
        response += "All pins locations:\n"
        for note in notes:
            if note['is_pinned'] == True:
                response += str(note['x'])+','+str(note['y'])+'\n'
    # Condition 2 GET color=red contains=4,6 refersTo=Fred
    else:
        # Loop through each request parameter after GET
        filtered_notes = []
        is_filtered = False
        for item in request[1:]:
            print(item)
            # item without '=' is invalid
            if '=' not in item:
                response += 'Invalid pair: {}, skiping to next'.format(item)
                continue
            param, value = enumerate(item.split('='))
            param,value = param[1].upper(), value[1].upper()
            print(param,value)
            # COLOR
            if param == GET_REQ_PARAMS[0]:
                filtered_notes = list(filter(lambda n: n['color']==value, filtered_notes))
                is_filtered = True
            # CONTAINS
            elif param == GET_REQ_PARAMS[1]:
                pos = value.split(',')
                print(pos)
                if len(pos)!=2:
                    response = 'Invalid coordinates/formatting. Please retry and follow format x,y (no space).'
                    break
                x,y = int(pos[0]), int(pos[1])
                filtered_notes = list(filter(lambda n: n['x']==x and n['y']==y, filtered_notes))
                is_filtered = True
            # REFERSTO
            elif param == GET_REQ_PARAMS[2]:
                filtered_notes = list(filter(lambda n: value in n['message'].upper(), filtered_notes))
                is_filtered = True
            # Invalid param
            else:
                response = 'Invalid GET parameter: {}\n'.format(item)
                return response
            # If after any item search the filtered_notes is empty, exit loop
            if is_filtered and filtered_notes == []:
                break
        response += 'Notes that satify criteria {}:\n'.format(request[1:])
        if is_filtered and len(filtered_notes) > 0:
            for n in filtered_notes:
                response += '{},{} - {}\n'.format(n['x'], n['y'], n['message'])
        else:
            response += 'No qualified notes found.'
    return response

def socket_service(connection_socket):
    global notes

    while connection_socket:
        print('Server is ready to receive requests')
        # Get request content
        request = connection_socket.recv(1024).decode().split()
        request_code = request[0].upper()
        print(request)

        if request_code == 'CONNECT':
            response=server_connect()
        elif request_code == 'DISCONNECT':
            connection_socket.close()
            break
        elif request_code == 'CLEAR':
            response, notes = server_clear(notes)
        elif request_code in ('PIN','UNPIN'):
            response = server_pin_unpin(request, request_code)
        elif request_code == 'POST':
            response, notes = server_post(request, notes)
        elif request_code == 'GET':
            response = server_get(request, notes)
        # Sent the response message to client
        connection_socket.send(response.encode())



if __name__ == "__main__":

    DEFAULT_PIN_STATUS = False
    GET_REQ_PARAMS = ['COLOR','CONTAINS','REFERSTO']

    try:
        # User inputs
        # If more than 3 args entered, proceed with cmd inputs
        if len(sys.argv) >= 5:
            args = sys.argv
            arg1 = args[1]
            arg2 = args[2]
            arg3 = args[3]
            # Exit if args are invalid
            if not arg1.isdigit() or not arg2.isdigit() or not arg3.isdigit():
                print('Arguments not valid. Example: python3 test.py 8080 100 100 ...')
                sys.exit()
            elif int(arg1)==0 or int(arg2)==0 or int(arg3)==0:
                print('First 3 args should be integers greater than 0. Example: python3 test.py 8080 100 100')
                sys.exit()
            else:
                SERVER_PORT = abs(int(arg1))
                BOARD_WIDTH = abs(int(arg2))
                BOARD_HEIGHT = abs(int(arg3))
                AVAIL_COLORS = args[4:]
        # If number of args is less than 3, ask for input explicitly
        elif len(sys.argv) < 5:
            SERVER_PORT = int(input('Enter an available port number: '))
            BOARD_WIDTH = int(input('Enter note board width: '))
            BOARD_HEIGHT = int(input('Enter note board height: '))
            AVAIL_COLORS = input(
                'Enter note color options separated by space (first input as default colour): ').upper().split()
        DEFAULT_COLOR = AVAIL_COLORS[0]
        #This note will be global among all threads
        notes = []
        # Create a TCP server socket
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(("", SERVER_PORT))
        thread_limit = 5
        server_socket.listen(thread_limit)
        print('Server is ready')

        # Server should be up and running and listening to the incoming connections
        while True:
            print('Current active threads count:', active_count())
            while active_count() == thread_limit:
                print('{} alive, waiting for any to finish to continue opening a new connection...')
                sleep(5)
                continue
            # (Wait to) Set up a new connection from the client
            connection_socket, addr = server_socket.accept()
            print(connection_socket)
            print(addr)
            connection_thread = Thread(target=socket_service, args=(connection_socket,))
            connection_thread.start()
            # print('one connection ended')
            
    except Exception as e:
        print(e)
    finally:
        server_socket.close()
        sys.exit()  # Terminate the program after sending the corresponding data
