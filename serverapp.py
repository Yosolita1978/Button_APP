from __future__ import print_function
import httplib2
import os
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
from send_sms import send_SMS
import json

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
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_locations():
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
    location = results[0]['geometry']['location']
    print(address)
    print((location['lat'], location['lng']))
    return (location['lat'], location['lng'])


def get_geocodes_home():
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


def get_user_credentials_from_file():

    with open("lyft_secret.json", 'r') as f:
        credential = json.loads(f.read())

    return OAuth2Credential(**credential)


def get_user_credentials_from_oauth_flow():

    PERMISSION_SCOPES = ['public', 'rides.read', 'offline', 'rides.request', 'profile']

    auth_flow = AuthorizationCodeGrant(CLIENT_ID, CLIENT_SECRET, PERMISSION_SCOPES)
    auth_url = auth_flow.get_authorization_url()
    print(auth_url)
    redirect_url = raw_input("Please type here the redirect url: ")

    session = auth_flow.get_session(redirect_url)
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

    with open("lyft_secret.json", 'w') as f:
        f.write(json.dumps(credential_data))

    return credential


def get_lyft_client():

    try:
        credential = get_user_credentials_from_file()

    except IOError:
        credential = get_user_credentials_from_oauth_flow()

    session = Session(oauth2credential=credential)
    return LyftRidesClient(session)


if __name__ == '__main__':
    home = get_geocodes_home()
    latitude_home = home[0]
    longitude_home = home[1]

    myclient = get_lyft_client()
    response = myclient.get_ride_types(home[0], home[1])
    ride_types = response.json.get('ride_types')
    my_ride_type = ride_types[1]['ride_type']

    next_event = get_locations()
    if not next_event:
        print("Sorry, your next event doesn't have an address")

    else:
        address = get_latitud_longitude(next_event)
        final_latitud = address[0]
        final_longitud = address[1]

        response = myclient.request_ride(
            ride_type=my_ride_type,
            start_latitude=latitude_home,
            start_longitude=longitude_home,
            end_latitude=final_latitud,
            end_longitude=final_longitud)

        ride_details = response.json
        lyft = ride_details['ride_type']
        lyft_id = ride_details['ride_id']
        message = "Your %s with the id %s has been authorized" % (lyft, lyft_id)
        print(send_SMS(message))


