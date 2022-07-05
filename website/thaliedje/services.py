import logging
from datetime import timedelta
from json import JSONDecodeError

from spotipy import SpotifyException
from .spotify import SpotifyCache

from django.utils import timezone

from thaliedje.models import (
    SpotifyArtist,
    SpotifyTrack,
    SpotifyQueueItem,
    ThaliedjeBlacklistedUser,
)


def user_is_blacklisted(user):
    """Return if the user is on the blacklist."""
    return ThaliedjeBlacklistedUser.objects.filter(user=user).exists()


def create_track_database_information(track_info):
    """
    Get and create database information for tracks.

    :param track_info: the track information from the spotify API
    :return: a SpotifyTrack object holding the track_info
    """
    artist_models = create_artists_information(track_info["artists"])
    return create_track_information(track_info["name"], track_info["id"], artist_models)


def create_artists_information(artists_info):
    """
    Get and create a list of artists.

    :param artists_info: the artist information from the spotify API
    :return: a list of SpotifyArtist objects holding the artists_info
    """
    artist_models = list()
    for x in artists_info:
        artist_model, _ = SpotifyArtist.objects.get_or_create(artist_id=x["id"])
        if artist_model.artist_name != x["name"]:
            artist_model.artist_name = x["name"]
            artist_model.save()
        artist_models.append(artist_model)
    return artist_models


def create_track_information(track_name, track_id, artist_models):
    """
    Get and create track information.

    :param track_name: the track name
    :param track_id: the track id
    :param artist_models: a list of SpotifyArtist objects
    :return: a SpotifyTrack object holding the input information
    """
    track_model, _ = SpotifyTrack.objects.get_or_create(track_id=track_id)
    updated = False

    if track_model.track_name != track_name:
        track_model.track_name = track_name
        updated = True

    if set(track_model.track_artists.all()) != set(artist_models):
        [track_model.track_artists.add(x) for x in artist_models]
        updated = True

    if updated:
        track_model.save()

    return track_model


def search_tracks(query, player, maximum=5):
    """
    Search SpotifyTracks for a search query.

    :param query: the search query
    :param player: the player
    :param maximum: the maximum number of results to search for
    :return: a list of tracks [{"name": the trackname, "artists": [a list of artist names],
     "id": the Spotify track id}]
    """
    try:
        result = player.spotify.search(query, limit=maximum, type="track")
    except SpotifyException as e:
        logging.error(e)
        raise e

    # Filter out None values as the Spotipy library might return None for data it can't decode
    result = [x for x in result["tracks"]["items"] if x is not None]
    result = sorted(result, key=lambda x: -x["popularity"])
    trimmed_result = [{"name": x["name"], "artists": [y["name"] for y in x["artists"]], "id": x["id"]} for x in result]
    return trimmed_result


def request_song(user, player, spotify_track_id):
    """
    Request a track for a player.

    :param user: the user requesting the track
    :param player: the player
    :param spotify_track_id: the Spotify track id to request
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        track_info = player.spotify.track(spotify_track_id)
        player.spotify.add_to_queue(spotify_track_id, device_id=player.playback_device_id)
        track = create_track_database_information(track_info)
        SpotifyQueueItem.objects.create(
            track=track,
            player=player,
            requested_by=user,
        )
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_start(player):
    """
    Start playing on the playback device of a Player.

    :param player: the player
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        SpotifyCache.instance(player.id).start_playback(player)
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_pause(player):
    """
    Pause the playback device of a Player.

    :param player: the player
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        SpotifyCache.instance(player.id).pause_playback(player)
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_next(player):
    """
    Skip to the next song in the playback device queue of a Player.

    :param player: the player
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.next_track()
        SpotifyCache.instance(player.id).reset()
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_previous(player):
    """
    Go back to the previous song in the playback device queue of a Player.

    :param player: the player
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.previous_track()
        SpotifyCache.instance(player.id).reset()
    except SpotifyException as e:
        logging.error(e)
        raise e


def get_player_volume(player):
    """
    Get the volume of a player.

    :param player: the player
    :return: the volume
    :raises: SpotifyException on failure
    """
    try:
        current_playback = SpotifyCache.instance(player.id).current_playback(player)
        return current_playback["device"]["volume_percent"] if current_playback is not None else None
    except SpotifyException as e:
        logging.error(e)
        raise e


def set_player_volume(player, volume_percent):
    """
    Set the volume of a Player.

    :param player: the player
    :param volume_percent: the volume percentage
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.volume(volume_percent, device_id=player.playback_device_id)
        SpotifyCache.instance(player.id).reset()
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_currently_playing(player):
    """
    Get currently playing music information.

    :return: a dictionary with the following content:
        image: [link to image of track],
        name: [name of currently playing track],
        artists: [list of artist names],
        is_playing: [True|False]
    """
    if not player.configured:
        raise RuntimeError("This Spotify account is not configured yet.")

    try:
        # Use cache if available
        currently_playing = SpotifyCache.instance(player.id).currently_playing(player)
    except JSONDecodeError:
        currently_playing = None
    except OSError:
        currently_playing = None

    if currently_playing is None or currently_playing["currently_playing_type"] == "unknown":
        return False

    image = currently_playing["item"]["album"]["images"][0]["url"]
    name = currently_playing["item"]["name"]
    artists = [x["name"] for x in currently_playing["item"]["artists"]]

    return {
        "image": image,
        "name": name,
        "artists": artists,
        "is_playing": currently_playing["is_playing"],
    }


def execute_data_minimisation(dry_run=False):
    """
    Remove song-request history from users that is more than 31 days old.

    :param dry_run: does not really remove data if True
    :return: list of users from who data is removed
    """
    delete_before = timezone.now() - timedelta(days=31)
    requests = SpotifyQueueItem.objects.filter(added__lte=delete_before)

    users = []
    for request in requests:
        users.append(request.requested_by)
        request.requested_by = None
        if not dry_run:
            request.save()
    return users
