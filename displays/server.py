"""
(C) 2016 Julian Metzler

This file contains the classes needed to operate a server which controls
multiple displays. The server operates on a simple JSON-based protocol.
The full protocol specification can be found in the SERVER_PROTOCOL.md file.
The server runs as two threads; one to listen for messages and one
to control the displays.
"""

import json
import socket
import time
import traceback

from .error import DisplayServerError
from .display_bitmap import BitmapDisplay

def receive_message(sock):
  """
  Receive and parse an incoming message (prefixed with its length).
  
  sock:
  The socket to receive the message on
  """
  
  try:
    length = int(sock.recv(5))
    raw_data = bytearray()
    l = 0
    while l < length:
      part_data = sock.recv(4096)
      raw_data += part_data
      l += len(part_data)
    message = json.loads(raw_data.decode('utf-8'))
  except:
    raise
  return message

def send_message(sock, data):
  """
  Build and send a message (prefixed with its length).
  
  sock:
  The socket to send the message on
  
  data:
  The data to send
  """
  
  raw_data = json.dumps(data)
  length = len(raw_data)
  message = "{0:05d}{1}".format(length, raw_data)
  sock.sendall(message.encode('utf-8'))

def discard_message(sock):
  """
  Receive a message, but discard it.
  
  sock:
  The socket to receive the message on
  """
  
  sock.setblocking(False)
  try:
    while True:
      sock.recv(1024)
  except socket.error:
    pass
  finally:
    sock.setblocking(True)

class DisplayServer:
  def __init__(self, manager, port = 1820, allowed_ip_match = None,
    verbose = False):
    """
    manager:
    The DisplayManager instance associated with this server
    
    port:
    The network port to listen on
    
    allowed_ip_match:
    A list of IPs to allow messages from, no checks will be performed
    if this is None
    
    verbose:
    Whether to enable debug output
    """
    
    self.running = False
    self.manager = manager
    self.port = port
    self.allowed_ip_match = allowed_ip_match
    self.verbose = verbose
    
    # Generate the named display map
    self.displays = {}
    for port, display in self.manager.displays.items():
      self.displays[display.name] = display

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Prevent having to wait between reconnects
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  def output_verbose(self, text):
    """
    Output a text to the console only if debug output is enabled.
    
    text:
    The text to output
    """
    
    if self.verbose:
      print(text)
  
  def run(self):
    """
    Run the server.
    """
    
    self.output_verbose("Starting server...")
    self.running = True
    self.network_listen()
  
  def stop(self):
    """
    Stop the server.
    """
    
    self.output_verbose("Stopping server...")
    self.running = False
  
  def network_listen(self):
    """
    Monitor the socket for connections and receive messages.
    """
    
    self.socket.bind(('', self.port))
    self.socket.settimeout(5.0)
    self.output_verbose("Listening on port {0}".format(self.port))
    self.socket.listen(1)
    
    try:
      while self.running:
        try:
          # Wait for someone to connect
          conn, addr = self.socket.accept()
          ip, port = addr
          if self.allowed_ip_match is not None and \
          not ip.startswith(self.allowed_ip_match):
            self.output_verbose(
              "Discarding message from {0} on port {1}".format(*addr))
            discard_message(conn)
            continue
          
          self.output_verbose(
            "Receiving message from {0} on port {1}".format(*addr))
          # Receive the message(s)
          messages = receive_message(conn)
          if messages is None:
            # We received an invalid message, just discard it
            continue
          
          # If only a single message was passed, make a list of it
          if type(messages) not in (list, tuple):
            messages = [messages]
          
          # Collect the replies to the messages and send them all back
          reply = []
          for message in messages:
            reply.append(self.process_message(message))
          
          if reply:
            send_message(conn, reply)
        except socket.timeout: # Just renew the socket every few seconds
          pass
        except KeyboardInterrupt:
          raise
        except:
          traceback.print_exc()
    except KeyboardInterrupt:
      self.stop()
    finally:
      self.socket.close()
  
  def process_message(self, message):
    """
    Process an incoming message.
    
    message:
    The message to process
    """
    
    action = message.get('action', 'display')
    if action == 'hwconfig':
      # Query hardware configuration
      hwconfig = {}
      for name, display in self.displays.items():
        hwconfig[name] = {
          'port': display.port,
          'type': display.__class__.__name__,
          'description': str(display)
        }
        if issubclass(type(display), BitmapDisplay):
          hwconfig[name].update({
            'bitmap_width': display.bitmap_width,
            'bitmap_height': display.bitmap_height,
            'width': display.width,
            'height': display.height
          })
      return {'error': None, 'data': hwconfig}
    elif action == 'display':
      # Interface with a display
      display_name = message.get('display')
      if not display_name:
        return {'error': "No display specified"}
      
      display = self.displays.get(display_name)
      if not display:
        return {'error': "Display '{0}' does not exist".format(display_name)}
      
      func_name = message.get('func')
      if not func_name:
        return {'error': "No function specified"}
      
      func = getattr(display, func_name, None)
      if not func:
        return {'error': "Display '{0}' has no function '{1}'".format(
          display_name, func_name)}
      
      args = message.get('args', [])
      kwargs = message.get('kwargs', {})
      
      try:
        data = func(*args, **kwargs)
      except:
        if self.verbose:
          traceback.print_exc()
        return {'error': "Exception occurred during function call"}
      else:
        return {'error': None, 'data': data}


class DisplayClient:
  def __init__(self, host, port = 1820, timeout = 10.0):
    """
    host:
    The network address of the server to connect to
    
    port:
    The network port to use
    
    timeout:
    The network timeout
    """
    
    self.host = host
    self.port = port
    self.timeout = timeout
    self.queue = []

  def __getattr__(self, key):
    """
    This is used to map method calls that are not explicitly defined here
    to the corresponding display function calls to ease access to them
    """

    def _interface_mapper(display, *args, **kwargs):
      self.interface(display, key, *args, **kwargs)
    
    return _interface_mapper

  def send_raw_message(self, message, expect_reply = True):
    """
    Send a message to the server.
    
    message:
    The message to be sent
    
    expect_reply:
    Whether to wait for a reply from the server
    """
    
    reply = None
    try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(self.timeout)
      sock.connect((self.host, self.port))
      send_message(sock, message)
      
      if expect_reply:
        reply = receive_message(sock)
    finally:
      sock.close()
    return reply
  
  def clear_queue(self):
    """
    Delete all pending messages from the queue.
    """
    
    self.queue = []
  
  def sendall(self):
    """
    Send all pending messages to the server.
    """
    
    """# Append commits for every display
    displays = []
    for message in self.queue:
      display = message.get('display')
      if display and display not in displays:
        displays.append(display)
    
    for display in displays:
      self.queue.append(self.build_interface_message(display, 'commit'))"""
    
    if self.queue:
      replies = self.send_raw_message(self.queue)
      self.clear_queue()
      return replies
    else:
      return False

  ######################### LEVEL 1 MESSAGES
  
  def build_hwconfig_message(self):
    return {'action': 'hwconfig'}
  
  def build_interface_message(self, display, func, *args, **kwargs):
    return {
      'action': 'display',
      'display': display,
      'func': func,
      'args': args,
      'kwargs': kwargs
    }

  #########################
  
  def get_hwconfig(self):
    return self.send_raw_message(
      self.build_hwconfig_message())

  #########################
  
  def interface(self, display, func, *args, **kwargs):
    self.queue.append(
      self.build_interface_message(display, func, *args, **kwargs))