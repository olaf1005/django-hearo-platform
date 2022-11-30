"""
Jawnmower is a simple caching utility for caching information.
Basically it stores and reads objects things in .json files

This is for things that use the database a lot but don't need to
be updated all the time - you can cron a script to run every once in a while,
and cache its results in jawnmower, then read those results later when
a user opens some page that wants that information.

There are just two main methods:

write_json_cache
Example:
write_json_cache("worldmap_countries", {
  "US": 240,
  "AU": 12,
  "CA": "2"
}
=> True

This would write a .json file in HEARO_ROOT/jawnmower/json called
"worldmap_countries.json"


read_json_cache
Example:
read_json_cache("worldmap_countries")
=> {
  "US": 240,
  "AU": 12,
  "CA": "2"
}

This just gets the cached data under that name and parses them into a Python
dict

Use this to avoid redundantly doing enormous calculations/object counts of
site-wide data, which is slower than just reading a json file.

You need to set up your own script to do that and crontab it though.

Think about:

- making a communal script that anyone can add jawnmower operations to
that runs every half hour or something. For now, no such script exists.

"""
import json
import settings.utils as setting_utils


def get_cache_file_path(name):
    return setting_utils.project_path("jawnmower/json/{}.json".format(name))


def write_json_cache(name, data):
    # I/P:
    #   name: str
    #   data: dict
    # O/P:
    #   True

    fn = get_cache_file_path(name)
    f = open(fn, "w")
    json_data = json.dumps(data, separators=(",", ":"))
    f.write(json_data)
    f.close()
    return True


def read_json_cache(name):
    # I/P:
    #   name: str
    # O/P:
    #   a dict, the data
    fn = get_cache_file_path(name)
    try:
        f = open(fn, "r")
        data = f.read()
        data_as_py = json.loads(data)
        f.close()
        return (data_as_py, data)
    except:
        return (None, "")
