from __future__ import print_function
import boto3
import httplib2
from secret import *
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import requests
import datetime
from lyft_rides.auth import AuthorizationCodeGrant
from lyft_rides.client import LyftRidesClient
from lyft_rides.session import Session
from lyft_rides.session import OAuth2Credential
from lyft_rides.errors import ClientError
from send_sms import send_SMS
import json
from decimal import Decimal
from time import time

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Buttton'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    def default(obj):
        if isinstance(obj, Decimal):
            return int(obj)
        raise TypeError

    credential_data = load_from_storage('GoogleCredential')
    credential_json = json.dumps(credential_data, default=default)

    credentials = client.Credentials.new_from_json(credential_json)

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_next_event_location():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a string with the location of the next event in my calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=1, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')

    if not 'location' in events[0]:
        #print("Next event doesn't have a location")
        return None

    else:
        location = events[0]['location']
        if not location:
            print('No upcoming locations found.')
        return location


def get_latitud_longitude(address):
    """Basic usage of the Google Maps requests.

    This function returns a tuple with the latitude and longitude of the addres of the next event.
    """

    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'sensor': 'false', 'address': address}
    r = requests.get(url, params=params)
    results = r.json()['results']
    if results:
        location = results[0]['geometry']['location']
        print(address)
        print((location['lat'], location['lng']))
        return (location['lat'], location['lng'])
    else:
        return None


def get_home_coordinates():
    """Basic usage of the Google Maps requests.

    This function returns a tuple with the latitude and longitude of my home.
    """

    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'sensor': 'false', 'address': address_home}
    r = requests.get(url, params=params)
    results = r.json()['results']
    location = results[0]['geometry']['location']
    print(address_home)
    print((location['lat'], location['lng']))
    return (location['lat'], location['lng'])


def load_from_storage(table_name):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    credential = table.get_item(Key={'serial_number': SERIAL_NUMBER})
    if not 'Item' in credential:
        raise IOError

    credential = credential['Item']
    credential.pop('serial_number')
    if table_name == 'LyftCredential':
        credential['expires_in_seconds'] = int(credential['expires_in_seconds']) - int(time()) 
        print('HERE the json came from storage')
        print(credential)

    return credential


def save_to_storage(table_name, credential_data):
    # pass
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    credential_data['serial_number'] = SERIAL_NUMBER
    print("this is the saving moment")
    print(credential_data)
    table.put_item(Item=credential_data)


def get_user_credentials_from_file():

    credential = load_from_storage('LyftCredential')

    return OAuth2Credential(**credential)


def get_user_credentials_from_oauth_flow(sandbox=True):

    PERMISSION_SCOPES = ['public', 'rides.read', 'offline', 'rides.request', 'profile']

    auth_flow = AuthorizationCodeGrant(
        CLIENT_ID,
        CLIENT_SECRET,
        PERMISSION_SCOPES,
        is_sandbox_mode=sandbox)
    auth_url = auth_flow.get_authorization_url()
    print(auth_url)
    redirect_url = raw_input("Please type here the redirect url: ")

    session = auth_flow.get_session(redirect_url)
    credential = session.oauth2credential

    return credential


def get_lyft_client(sandbox=True):

    try:
        credential = get_user_credentials_from_file()

    except IOError:
        credential = get_user_credentials_from_oauth_flow(sandbox)

    session = Session(oauth2credential=credential)
    client = LyftRidesClient(session)

    client.refresh_oauth_credential()

    credential = session.oauth2credential
    credential_data = {
        'client_id': credential.client_id,
        'access_token': credential.access_token,
        'expires_in_seconds': credential.expires_in_seconds,
        'scopes': list(credential.scopes),
        'grant_type': credential.grant_type,
        'client_secret': credential.client_secret,
        'refresh_token': credential.refresh_token,
    }

    save_to_storage('LyftCredential', credential_data)

    return client


def get_ride_type(lyft_client, start_coordinates):

    start_latitude, start_longitude = start_coordinates
    response = lyft_client.get_ride_types(start_latitude, start_longitude)
    ride_types = response.json.get('ride_types')
    lyft_type = ride_types[1]['ride_type']
    return lyft_type


def request_lyft_ride(lyft_client, start_coordinates, end_coordinates, ride_type, cost_token=None):

    start_latitude, start_longitude = start_coordinates
    end_latitude, end_longitude = end_coordinates

    response = lyft_client.get_cost_estimates(
        ride_type=ride_type,
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude)

    cost_json = response.json
    if cost_json['cost_estimates'][0]['cost_token']:
        cost_token = cost_json['cost_estimates'][0]['cost_token']

    # return 0

    response = lyft_client.request_ride(
        ride_type=ride_type,
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude,
        primetime_confirmation_token=cost_token)

    ride_details = response.json

    lyft_id = ride_details['ride_id']
    return lyft_id


def call_a_ride(sandbox=True):

    home_coordinates = get_home_coordinates()

    next_event_location = get_next_event_location()
    if not next_event_location:
        message = "Sorry, your next event doesn't have an address. Please, check your calendar"
        print(send_SMS(message))
        return

    next_event_coordinates = get_latitud_longitude(next_event_location)
    if not next_event_coordinates:
        message = "Sorry, your next event doesn't have a valid address."
        print(send_SMS(message))
        return

    try:
        my_client = get_lyft_client(sandbox)
        ride_type = get_ride_type(my_client, home_coordinates)
        ride_id = request_lyft_ride(my_client, home_coordinates, next_event_coordinates, ride_type)

    except ClientError, e:
        print(e)
        message = "The access token from lyft expired"
        print(send_SMS(message))
        return

    message = "Your %s with the id %s has been authorized" % (ride_type, ride_id)
    print(send_SMS(message))


def lambda_handler(event, context):

    call_a_ride(sandbox=False)

if __name__ == '__main__':
    call_a_ride(sandbox=False)
