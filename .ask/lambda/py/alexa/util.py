# -*- coding: utf-8 -*-

"""Utility module to generate text for commonly used responses."""
import random
import six
import nltk
import re
import os
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup


from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type

from . import data

#import textblob
#from textblob import TextBlob

def get_random_state(states_list):
    """Return a random value from the list of states."""
    return random.choice(states_list)


def state_properties():
    """Return the list of state properties."""
    val = ["abbreviation", "capital", "statehood_year",
           "statehood_order"]
    return val


def get_random_state_property():
    """Return a random state property."""
    return random.choice(state_properties())


def get_card_description(item):
    """Return the description shown on card in Alexa response."""
    text = "State Name: {}\n".format(item['state'])
    text += "State Capital: {}\n".format(item['capital'])
    text += "Statehood Year: {}\n".format(item['statehood_year'])
    text += "Statehood Order: {}\n".format(item['statehood_order'])
    text += "Abbreviation: {}\n".format(item['abbreviation'])
    return text


def supports_display(handler_input):
    # type: (HandlerInput) -> bool
    """Check if display is supported by the skill."""
    try:
        if hasattr(
                handler_input.request_envelope.context.system.device.
                        supported_interfaces, 'display'):
            return (
                    handler_input.request_envelope.context.system.device.
                    supported_interfaces.display is not None)
    except:
        return False


def get_bad_answer(item):
    """Return response text for incorrect answer."""
    return "{} {}".format(data.BAD_ANSWER.format(item), data.HELP_MESSAGE)


def get_current_score(score, counter):
    """Return the response text for current quiz score of the user."""
    return data.SCORE.format("current", score, counter)


def get_final_score(score, counter):
    """Return the response text for final quiz score of the user."""
    return data.SCORE.format("final", score, counter)


def get_card_title(item):
    """Return state name as card title."""
    return item["state"]


def get_image(ht, wd, label):
    """Get flag image with specified height, width and state abbr as label."""
    return data.IMG_PATH.format(str(ht), str(wd), label)


def get_small_image(item):
    """Get state flag small image (720x400)."""
    return get_image(720, 400, item['abbreviation'])


def get_large_image(item):
    """Get state flag large image (1200x800)."""
    return get_image(1200, 800, item['abbreviation'])


def get_speech_description(item):
    """Return state information in well formatted text."""
    return data.SPEECH_DESC.format(
        item['state'], item['statehood_order'], item['statehood_year'],
        item['state'], item['capital'], item['state'], item['abbreviation'],
        item['state'])


def get_ordinal_indicator(counter):
    """Return st, nd, rd, th ordinal indicators according to counter."""
    if counter == 1:
        return "1st"
    elif counter == 2:
        return "2nd"
    elif counter == 3:
        return "3rd"
    else:
        return "{}th".format(str(counter))


def __get_attr_for_speech(attr):
    """Helper function to convert attribute name."""
    return attr.lower().replace("_", " ").strip()


def get_question_without_ordinal(attr, item):
    return "What is the {} of {}. ".format(
        __get_attr_for_speech(attr), item["state"])

def get_my_question_without_ordinal(attr, item):
    return "{}".format(item["q"])

def get_my_question(counter, attr, item):
    return (
        "Here is your {} question. {}").format(
        get_ordinal_indicator(counter),
        get_my_question_without_ordinal(attr, item))

def get_question(counter, attr, item):
    """Return response text for nth question to the user."""
    return (
        "Here is your {} question. {}").format(
        get_ordinal_indicator(counter),
        get_question_without_ordinal(attr, item))

def get_my_answer(attr, item):
    """Return response text for correct answer to the user."""
    return "The answer is {}. ".format(
        item["a"])

def get_answer(attr, item):
    """Return response text for correct answer to the user."""
    if attr.lower() == "abbreviation":
        return ("The {} of {} is "
                "<say-as interpret-as='spell-out'>{}</say-as>. ").format(
            __get_attr_for_speech(attr), item["state"], item["abbreviation"])
    else:
        return "The {} of {} is {}. ".format(
            __get_attr_for_speech(attr), item["state"], item[attr.lower()])

def ask_my_question(handler_input):
    attr = handler_input.attributes_manager.session_attributes

    random_q = get_random_state(data.QUIZ_CONTENT)
    attr["quiz_item"] = random_q
    attr["quiz_attr"] = "a"
    attr["counter"] += 1

    handler_input.attributes_manager.session_attributes = attr

    return get_my_question(attr["counter"], attr["quiz_attr"], attr["quiz_item"])

def ask_question(handler_input):
    # (HandlerInput) -> None
    """Get a random state and property, return question about it."""
    random_state = get_random_state(data.STATES_LIST)
    random_property = get_random_state_property()

    attr = handler_input.attributes_manager.session_attributes

    attr["quiz_item"] = random_state
    attr["quiz_attr"] = random_property
    attr["counter"] += 1

    handler_input.attributes_manager.session_attributes = attr

    return get_question(attr["counter"], random_property, random_state)


def get_speechcon(correct_answer):
    """Return speechcon corresponding to the boolean answer correctness."""
    text = ("<say-as interpret-as='interjection'>{} !"
            "</say-as><break strength='strong'/>")
    if correct_answer:
        return text.format(random.choice(data.CORRECT_SPEECHCONS))
    else:
        return text.format(random.choice(data.WRONG_SPEECHCONS))


def get_multiple_choice_answers(item, attr, states_list):
    """Return multiple choices for the display to show."""
    answers_list = [item[attr]]
    # Insert the correct answer first

    while len(answers_list) < 3:
        state = random.choice(states_list)

        if not state[attr] in answers_list:
            answers_list.append(state[attr])

    random.shuffle(answers_list)
    return answers_list


def get_item(slots, states_list):
    """Get matching data object from slot value."""
    item = []
    resolved_slot = None
    for _, slot in six.iteritems(slots):
        if slot.value is not None:
            resolved_slot = slot.value
            for state in states_list:
                for _, v in six.iteritems(state):
                    if v.lower() == slot.value.lower():
                        item.append(state)
            if len(item) > 0:
                return item[0], True
    else:
        return resolved_slot, False


def compare_token_or_slots(handler_input, value):
    """Compare value with slots or token,
        for display selected event or voice response for quiz answer."""
    if is_request_type("Display.ElementSelected")(handler_input):
        return handler_input.request_envelope.request.token == value
    else:
        return compare_slots(
            handler_input.request_envelope.request.intent.slots, value)


def compare_slots(slots, value):
    """Compare slot value to the value provided."""
    for _, slot in six.iteritems(slots):
        if slot.value is not None:
            return slot.value.lower() == value.lower()
    else:
        return False

# Create the blank in string
def replaceIC(word, sentence):
    insensitive_hippo = re.compile(re.escape(word), re.IGNORECASE)
    return insensitive_hippo.sub('blank', sentence)

# For a sentence create a blank space.
# It first tries to randomly selection proper-noun
# and if the proper noun is not found, it selects a noun randomly.
def removeWord(sentence, poss):
    words = None
    if len(poss) < 3:
        return (None, sentence, None)
    if 'NN' not in poss:
        return (None, sentence, None)
    if 'VBZ' not in poss:
        return (None, sentence, None)
    if 'NNP' in poss:
        words = poss['NNP']
    elif 'NN' in poss:
        words = poss['NN']
    else:
        print("NN and NNP not found")
        return (None, sentence, None)
    if len(words) > 0:
        word = random.choice(words)
        replaced = replaceIC(word, sentence)
        return (word, sentence, replaced)
    else:
        print("words are empty")
        return (None, sentence, None)


def setdata():
    ww2 = '''
    Daniel Robert Middleton[5] (born 8 November 1991), better known online as DanTDM (formerly TheDiamondMinecart), is an English YouTuber, gamer, actor and author known for his video game commentaries.[6] His online video channels have covered many video games including Minecraft, Roblox and Pokémon.
    His channel has been listed among the top YouTube channels in the United Kingdom.[7] In July 2015, he was listed as one of the most popular YouTubers in the world by viewership.[8] He has won several Kids' Choice Awards and set Guinness World Records for his gaming and presenting. In 2017, Middleton topped the Forbes list of Highest-Paid YouTube Stars, earning $16.5 million (about GB£12.2 million) in one year. As of November 2020, his YouTube channel has reached over 24 million subscribers,     17 billion video views, and has posted more than 3,400 videos.
    '''
    url = "https://en.wikipedia.org/wiki/Meteorological_history_of_Hurricane_Dorian"
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    ww2 = soup.text

    return ww2

def initdata():
    ww2 = setdata()
    #ww2 = unicode(ww2, 'utf-8')
    os.environ["NLTK_DATA"] = "/tmp"
#    nltk.download('punkt', download_dir='/tmp')
    nltk.download('popular', download_dir='/tmp')
    nltk.data.path.append("/tmp")
    ww2b = TextBlob(ww2)
    print(ww2b)

    sposs = {}
    for sentence in ww2b.sentences:

        # We are going to prepare the dictionary of parts-of-speech as the key and value is a list of words:
        # {part-of-speech: [word1, word2]}
        # We are basically grouping the words based on the parts-of-speech
        poss = {}
        sposs[sentence.string] = poss;
        for t in sentence.tags:
            tag = t[1]
            if tag not in poss:
                poss[tag] = []
            poss[tag].append(t[0])

    # Iterate over the sentenses
    for sentence in sposs.keys():
        poss = sposs[sentence]
        (word, osentence, replaced) = removeWord(sentence, poss)
        if replaced is None:
            print ("Founded none for ")
            print(sentence)
        else:
            quizentry = {}
            quizentry['q'] = replaced
            quizentry['a'] = word
            data.QUIZ_CONTENT.append(quizentry)
