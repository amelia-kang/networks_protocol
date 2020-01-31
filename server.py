# Import socket module
from socket import socket, AF_INET, SOCK_STREAM
import sys  # In order to terminate the program
# from threading 

DEFAULT_PIN_STATUS = False
GET_REQ_PARAMS = ['COLOR','CONTAINS','REFERSTO']

def socket_service(connection_socket):
    global notes

    while connection_socket:
        print('Server is ready to receive requests')
        # Get request content
        request = connection_socket.recv(1024).decode().split()
        request_code = request[0].upper()
        print(request)

        if request_code == 'CONNECT':
            response = 'Available colors for notes: ' + \
                str(avail_colors) + '\nBoard size: ' + \
                str((board_width, board_height))

        elif request_code == 'DISCONNECT':
            connection_socket.close()
            break
        
        elif request_code == 'CLEAR':
            init_len = len(notes)
            notes = list(filter(lambda n: n['is_pinned']==True, notes))
            response = "{} notes without pins removed".format(init_len-len(notes))

        elif request_code in ('PIN','UNPIN'):
            pin_count = 0
            response = ''
            if len(request)==2 and ',' in request[1]:
                coords = request[1].split(',')
                x,y = int(coords[0]), int(coords[1])
                for note in notes:
                    if note['x']==x and note['y']==y:
                        if request_code == 'PIN':
                            if note['is_pinned'] == True:
                                response += 'Note at {},{} already pinned'.format(x,y)
                            else:
                                note['is_pinned'] = True
                                pin_count+=1
                        else:
                            if note['is_pinned'] == False:
                                response += 'Note at {},{} already not pinned'.format(x,y)
                            else:
                                note['is_pinned'] = False
                                pin_count+=1
                response += '{} note(s) {}.'.format(pin_count, 'pinned' if request_code=='PIN' else 'unpinned')

        elif request_code == 'POST':
            response = ''
            try:
                x = int(request[1])
                y = int(request[2])
                width = int(request[3])
                height = int(request[4])
                if x<0 or y<0 or y>board_height or width > board_width or height>board_height:
                    raise Exception("Note does not fit on the board. Please resize/re-position to fit it in {}x{}.".format(board_width, board_height))

                color = request[5]
                # If the value at index 5 is not in available color list, set it to None
                if color.upper() not in avail_colors:
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
                color = default_color if not color else color

                # Create note in dictionary
                note = {'x':x, 'y':y, 'width':width, 'height':height, 'color':color.upper(), 'message':message, 'is_pinned':is_pinned}
                print('note:',note)
                notes.append(note)
                response += 'Note added to the board successfully.'
            except Exception as e:
                response = e

        elif request_code == 'GET':
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
                filtered_notes = notes
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
                    # CONTAINS
                    elif param == GET_REQ_PARAMS[1]:
                        pos = value.split(',')
                        print(pos)
                        if len(pos)!=2:
                            response = 'Invalid coordinates/formatting. Please retry and follow format x,y (no space).'
                            break
                        x,y = int(pos[0]), int(pos[1])
                        filtered_notes = list(filter(lambda n: n['x']==x and n['y']==y, filtered_notes))
                    # REFERSTO
                    elif param == GET_REQ_PARAMS[2]:
                        filtered_notes = list(filter(lambda n: value in n['message'].upper(), filtered_notes))
                    # Invalid param
                    else:
                        response = 'Invalid GET parameter: {}\n'.format(item)
                    # If after any item search the filtered_notes is empty, exit loop
                    if filtered_notes == []:
                        break
                response += 'Notes that satify above criteria {}:\n'.format(request[1:])
                if filtered_notes == []:
                    response += 'None'
                else:
                    for n in filtered_notes:
                        response += '{},{} {}\n'.format(n['x'], n['y'], n['message'])
                print(response)



                        
        connection_socket.send(response.encode())



if __name__ == "__main__":
    
    try:
        # User inputs
        sys.argv
        server_port = int(input('Enter an available port number: '))
        board_width = int(input('Enter note board width: '))
        board_height = int(input('Enter note board height: '))
        avail_colors = input(
            'Enter note color options separated by space (first input as default colour): ').upper().split()
        default_color = avail_colors[0]


        notes = []
        # Create a TCP server socket
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(("", server_port))
        server_socket.listen(1)
        print('Server is ready')

        # Server should be up and running and listening to the incoming connections
        while True:
            # (Wait to) Set up a new connection from the client
            connection_socket, addr = server_socket.accept()
            print(connection_socket)
            print(addr)

            socket_service(connection_socket)
            print('one connection ended')
            

        
    except Exception as e:
        print(e)
    finally:
        server_socket.close()
        sys.exit()  # Terminate the program after sending the corresponding data
