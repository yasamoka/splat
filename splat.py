import hashlib
import json

def __letters_idx(letters):
    if letters is None:
        return 0
    idx = 0
    for i in range(len(letters)):
        idx += (ord(letters[len(letters) - i - 1]) - ord('a')) * (26**i)
    return idx

def __letter_suffix(idx, end_suffix, start_suffix_idx):
    letter_suffix_chars = [None] * len(end_suffix)
    idx += start_suffix_idx
    for i in range(len(end_suffix)):
        div = 26 ** (len(end_suffix) - i - 1)
        letter_suffix_chars[i] = chr(ord('a') + idx // div)
        idx %= div
    letter_suffix = "".join(letter_suffix_chars)
    return letter_suffix

def __read_chunk(root_filepath, idx, end_suffix, start_suffix_idx, verbose):
    letter_suffix = __letter_suffix(idx, end_suffix, start_suffix_idx)
    chunk_filename = root_filepath + letter_suffix
    if verbose:
        print("Reading \"{}\" ...".format(chunk_filename), end='')
    with open(chunk_filename, 'rb') as chunk_file:
        chunk_data = chunk_file.read()
        if verbose:
            print(" done.", end='')
    return chunk_filename, chunk_data

def __hash_chunk_data(chunk_data, verbose):
    if verbose:
        print(" Hashing ...", end='')
    h = hashlib.sha1(chunk_data)
    if verbose:
        print(" done.", end='')
    return h.hexdigest()

def __load_json(json_filepath, verbose):
    if verbose:
        print("Opening \"{}\" for reading ...".format(json_filepath), end='')
    with open(json_filepath) as json_file:
        if verbose:
            print(" done.\nLoading data from JSON file ...", end='')
        json_dict = json.load(json_file)
        if verbose:
            print(" done.")
    end_suffix = json_dict["end_suffix"]
    start_suffix = json_dict["start_suffix"]
    end_suffix_idx = __letters_idx(end_suffix)
    start_suffix_idx = __letters_idx(start_suffix)
    num_of_files = end_suffix_idx - start_suffix_idx + 1
    hashes = json_dict["hashes"]
    assert len(hashes) == num_of_files
    return end_suffix, start_suffix, num_of_files, hashes

def hash(root_filepath, end_suffix, start_suffix=None, json_filepath="info.json", verbose=True):
    end_suffix_idx = __letters_idx(end_suffix)
    start_suffix_idx = __letters_idx(start_suffix)
    num_of_files = end_suffix_idx - start_suffix_idx + 1
    hashes = [None] * num_of_files
    for i in range(num_of_files):
        _, chunk_data = __read_chunk(root_filepath, i, end_suffix, start_suffix_idx, verbose)
        hashes[i] = __hash_chunk_data(chunk_data, verbose)
        print()
    json_dict = {
        'end_suffix': end_suffix,
        'start_suffix': start_suffix,
        'hashes': hashes
    }
    if verbose:
        print("Opening \"{}\" for writing ...".format(json_filepath), end='')
    with open(json_filepath, 'w') as json_file:
        if verbose:
            print(" done.\nSaving data to JSON file ...", end='')
        json.dump(json_dict, json_file)
        if verbose:
            print(" done.")

def validate(root_filepath, json_filepath="info.json", stop_at_mismatch=False, verbose=True):
    end_suffix, start_suffix, num_of_files, hashes = __load_json(json_filepath, verbose)
    start_suffix_idx = __letters_idx(start_suffix)
    mismatch_found = False
    mismatches = {}
    for i in range(num_of_files):
        chunk_filename, chunk_data = __read_chunk(root_filepath, i, end_suffix, start_suffix_idx, verbose)
        h = __hash_chunk_data(chunk_data, verbose)
        print()
        if h != hashes[i]:
            print("MISMATCH FOUND - Actual: {} | Expected: {}".format(h, hashes[i]))
            mismatches[chunk_filename] = (h, hashes[i])
            if stop_at_mismatch:
                return mismatches
            mismatch_found = True
    if verbose:
        if mismatch_found:
            print("Mismatches found at:")
            for chunk_filename in mismatches:
                actual_hash, expected_hash = mismatches[chunk_filename]
                print("{} - Actual: {} | Expected: {}".format(chunk_filename, actual_hash, expected_hash))
        else:
            print("All hashes match.")
    return mismatches

def join(root_filepath, target_filepath, json_filepath="info.json", hash=False, verbose=True):
    end_suffix, start_suffix, num_of_files, hashes = __load_json(json_filepath, verbose)
    start_suffix_idx = __letters_idx(start_suffix)
    if verbose:
        print("Opening \"{}\" for writing ...".format(target_filepath), end='')
    with open(target_filepath, 'wb') as target_file:
        if verbose:
            print(" done.")
        for i in range(num_of_files):
            chunk_filename, chunk_data = __read_chunk(root_filepath, i, end_suffix, start_suffix_idx, verbose)
            if hash:
                h = __hash_chunk_data(chunk_data, verbose)
                if h != hashes[i]:
                    if verbose:
                        print("\nMISMATCH FOUND - Actual: {} | Expected: {}".format(h, hashes[i]))
                    return {chunk_filename: (h, hashes[i])}
            if verbose:
                print(" Appending to {} ...".format(target_filepath), end='')
            target_file.write(chunk_data)
            if verbose:
                print(" done.")
    if verbose:
        print("Joined successfully.")
    if hash:
        return {}