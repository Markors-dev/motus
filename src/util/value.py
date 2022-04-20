

def int_list_in_order(int_list):
    """Checks if integers in list are in order

    i.e. [2, 3, 4] =True or [12, 15, 16] =False

    :param int_list <list(<int>, ...)>
    :return <bool>
    """
    int_list = sorted(int_list)
    for i in range(len(int_list) - 1):
        if int_list[i] + 1 != int_list[i + 1]:
            return False
    return True


def convert_to_title_format(sentence):
    """Convert sentence to 'title' format and returns it

    Replaces separator '_' with space ' ' and sets words in title format.

    :param sentence <str> Input sentence
    :return <str> Output sentence in title format
    """
    chunks = sentence.split('_')
    chunks_non_empty = list(filter(lambda x: len(x) > 0, chunks))
    sentence = ' '.join(chunks_non_empty).title()
    return sentence


def wrap_text(text, line_length=20):
    """Wraps text by insertion newline with given line length

    :param text <str> Input text
    :param line_length <int> Maximum line length
    :return <str> Wrapped text
    """
    all_words = [word + ' ' for word in text.split(' ') if word != '']
    curr_line = ''
    new_text = ''
    for word in all_words:
        if len(curr_line + word) <= line_length:
            curr_line += word
        else:
            new_text += curr_line + '\n'
            curr_line = word
    new_text += curr_line
    return new_text


def shorten_text(text, max_length):
    """Shortens a text if max text length is reached

    The middle of the text is replaced with '...'

    :param text <str> Input text
    :param max_length <int> Max length of text
    :return <str> Shorten text
    """
    assert max_length > 10, 'Param "max_length" must be bigger than 10'
    if len(text) <= max_length:
        return text
    replace_text = '...'
    first_part_len = (max_length - len(replace_text)) // 2
    last_part_len = max_length - first_part_len - len(replace_text)
    short_text = text[:first_part_len] + replace_text + text[-1 * last_part_len:]
    return short_text


def pad_text(text, min_len=15):
    """Pads text with whitespaces left and right of the text

    :param text <str> Input text
    :param min_len <int> Minimum padded text length
    :return <str> Padded text
    """
    if len(text) < min_len:
        diff = min_len - len(text)
        start_spaces = diff // 2
        end_spaces = diff - start_spaces
        new_text = f'{" " * start_spaces}{text}{" " * end_spaces}'
        return new_text
    else:
        # text is not smaller than "min_len"
        return text
