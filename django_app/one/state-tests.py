from state import HearoOneState
import sys


# TODO guarantee locations and genres exist


def assert_equal(a, b, name=""):
    if a == b:
        sys.stdout.write(".")
    else:
        print("\n%s FAILED" % name)
        print("expected: %s" % a)
        print("got:      %s" % b)


def run_test(test):
    url, params = test

    state_from_url = HearoOneState(url)
    state_from_params = HearoOneState(params)

    state_from_url_to_url = state_from_url.to_URL()
    state_from_params_to_url = state_from_params.to_URL()

    assert_equal(state_from_url_to_url, url)
    assert_equal(state_from_params_to_url, url)
    assert_equal(state_from_url.params, params)
    assert_equal(state_from_url.params, state_from_params.params)


tests = [
    # Basic nouns
    ("/producers/", {"noun": "producers"}),
    ("/bands/", {"noun": "bands"}),
    ("/musicians/", {"noun": "musicians"}),
    ("/fans/", {"noun": "fans"}),
    ("/venues/", {"noun": "venues"}),
    ("/songwriters/", {"noun": "songwriters"}),
    ("/djs/", {"noun": "djs"}),
    ("/sound-engineers/", {"noun": "sound engineers"}),
    (
        "/Canada/people-looking-for-a-band/",
        {"location": "Canada", "noun": "people looking for a band"},
    ),
    # Noun in location
    ("/Canada/djs/", {"noun": "djs", "location": "Canada"}),  # lol
    ("/Seattle,WA/musicians/", {"noun": "musicians", "location": "Seattle, WA"}),
    (
        "/Seattle,WA/people-looking-for-a-band/",
        {"noun": "people looking for a band", "location": "Seattle, WA"},
    ),
    ("/Seattle,WA/fans/", {"noun": "fans", "location": "Seattle, WA"}),
    (
        "/Colombia/people-looking-for-a-band/",
        {"noun": "people looking for a band", "location": "Colombia"},
    ),
    ("/Costa-Rica/producers/", {"noun": "producers", "location": "Costa Rica"}),
    ("/Seattle,WA/musicians/", {"noun": "musicians", "location": "Seattle, WA"}),
    # Genre
    ("/jazz/", {"genre": "jazz"}),
    # Genre in location
    ("/Seattle,WA/jazz/", {"genre": "jazz", "location": "Seattle, WA"}),
    ("/United-States/country/", {"genre": "country", "location": "United States"}),
    # Genre noun in location
    (
        "/Seattle,WA/musicians/jazz/",
        {"genre": "jazz", "noun": "musicians", "location": "Seattle, WA"},
    ),
    # Genre instrument noun in location
    (
        "/Seattle,WA/musicians/jazz/guitar/",
        {
            "genre": "jazz",
            "noun": "musicians",
            "location": "Seattle, WA",
            "instrument": "guitar",
        },
    ),
]


for test in tests:
    run_test(test)

print("\n")
