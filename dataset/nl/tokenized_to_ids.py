import argparse
import json
import gzip

def transform_to_ids(vocab_file, tokenized_file, output_file):
    # Load the vocabulary from the vocab_file
    with open(vocab_file, 'r') as f:
        vocab = json.load(f)

    # Create a reverse vocabulary, mapping id -> token
    reverse_vocab = {id: token for token, id in vocab.items()}

    # Open the tokenized file and the output file
    with open(tokenized_file, 'r') as tokenized_f, gzip.open(output_file, 'w') as output_f:
        # Iterate through each line in the tokenized file
        for line in tokenized_f:
            # Tokenize the line
            tokens = line.strip().split()
            # Convert the tokens to ids using the vocabulary
            ids = [vocab['<sos>']] + [vocab[token] for token in tokens] + [vocab['<eos>']]
            # Write the ids to the output file
            output_f.write(bytes(" ".join([str(id) for id in ids]) + "\n", "utf-8"))

if __name__ == "__main__":
    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("vocab_file", type=str, help="The vocabulary file (in JSON format)")
    parser.add_argument("tokenized_file", type=str, help="The tokenized file")
    parser.add_argument("output_file", type=str, help="The output file (will be gzip-compressed)")
    args = parser.parse_args()

    # Call the transform_to_ids function with the command-line arguments
    transform_to_ids(args.vocab_file, args.tokenized_file, args.output_file)
