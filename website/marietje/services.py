import logging
from datetime import timedelta
from spotipy import SpotifyException

from django.utils import timezone

from marietje.models import (
    SpotifyArtist,
    SpotifyTrack,
    SpotifyQueueItem,
)


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
    :param player: the SpotifyAccount (player)
    :param maximum: the maximum number of results to search for
    :return: a list of tracks [{"name": the trackname, "artists": [a list of artist names],
     "id": the Spotify track id}]
    """
    try:
        result = player.spotify.search(query, limit=maximum, type="track")
    except SpotifyException as e:
        logging.error(e)
        raise e

    result = sorted(result["tracks"]["items"], key=lambda x: -x["popularity"])
    trimmed_result = [
        {
            "name": x["name"],
            "artists": [y["name"] for y in x["artists"]],
            "id": x["id"],
        }
        for x in result
    ]
    return trimmed_result


def request_song(user, player, spotify_track_id):
    """
    Request a track for a player.

    :param user: the user requesting the track
    :param player: the SpotifyAccount (player)
    :param spotify_track_id: the Spotify track id to request
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        track_info = player.spotify.track(spotify_track_id)
        track = create_track_database_information(track_info)
        SpotifyQueueItem.objects.create(
            track=track, player=player, requested_by=user,
        )
        player.spotify.add_to_queue(
            spotify_track_id, device_id=player.playback_device_id
        )
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_start(player):
    """
    Start playing on the playback device of a SpotifyAccount.

    :param player: the SpotifyAccount (player)
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.start_playback(player.playback_device_id)
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_pause(player):
    """
    Pause the playback device of a SpotifyAccount.

    :param player: the SpotifyAccount (player)
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.pause_playback(player.playback_device_id)
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_next(player):
    """
    Skip to the next song in the playback device queue of a SpotifyAccount.

    :param player: the SpotifyAccount (player)
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.next_track()
    except SpotifyException as e:
        logging.error(e)
        raise e


def player_previous(player):
    """
    Go back to the previous song in the playback device queue of a SpotifyAccount.

    :param player: the SpotifyAccount (player)
    :return: Nothing
    :raises: SpotifyException on failure
    """
    try:
        player.spotify.previous_track()
    except SpotifyException as e:
        logging.error(e)
        raise e


def execute_data_minimisation(dry_run=False):
    """
    Remove song-request history from users that is more than 31 days old

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
