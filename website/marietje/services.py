from marietje.models import SpotifyArtist, SpotifyTrack


def create_track_database_information(track_info):
    artist_models = create_artists_information(track_info["artists"])
    return create_track_information(track_info["name"], track_info["id"], artist_models)


def create_artists_information(artists_info):
    artist_models = list()
    for x in artists_info:
        artist_model, _ = SpotifyArtist.objects.get_or_create(artist_id=x["id"])
        if artist_model.artist_name != x["name"]:
            artist_model.artist_name = x["name"]
            artist_model.save()
        artist_models.append(artist_model)
    return artist_models


def create_track_information(track_name, track_id, artist_models):
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
