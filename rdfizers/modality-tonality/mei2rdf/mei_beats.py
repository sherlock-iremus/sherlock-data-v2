from lxml import etree
from music21 import duration, stream, mei, note


def get_beats_data(score_xml):
    score = etree.tostring(score_xml, pretty_print=True)

    conv = mei.MeiToM21Converter(score)
    the_score = conv.run()

    identified_elements_beats_data = dict()
    score_beats = dict()

    for el in the_score.recurse():
        if type(el.id) == str and el.__class__ == note.Note:
            if type(el.duration) == duration.Duration:
                identified_elements_beats_data[el.id] = {
                    "duration_beats": el.duration.quarterLength/2,
                    "from_beat": el.beat,
                    "measure_number": el.measureNumber,
                    "to_beat": el.beat + el.duration.quarterLength/2,
                }
                if not el.measureNumber in score_beats:
                    score_beats[el.measureNumber] = list()
                score_beats[el.measureNumber].append(el.beat)
                score_beats[el.measureNumber] = sorted(list(set(score_beats[el.measureNumber])))

    for xmlid, data in identified_elements_beats_data.items():
        if not "beats" in data:
            data["beats"] = set()
            data["beats"].add(data["from_beat"])
        for _xmlid, _data in identified_elements_beats_data.items():
            if xmlid != _xmlid:
                if data["from_beat"] <= _data["from_beat"] and _data["from_beat"] < data["to_beat"]:
                    data["beats"].add(_data["from_beat"])

    for xmlid, data in identified_elements_beats_data.items():
        if "beats" in data:
            data["beats"] = list(sorted(data["beats"]))

    return {
        "score_beats": score_beats,
        "elements": identified_elements_beats_data
    }
