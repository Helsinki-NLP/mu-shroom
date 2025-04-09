#!/usr/bin/env python


def main(path_selections, outfile="selected_responses.jsonl"):
    with open(path_selections) as f:
        filenames = f.readlines()
    filenames = [x.strip("\r\n") for x in filenames]

    llm_response_files = set(filenames)
    llm_responses = {}
    for output_path in llm_response_files:
        with open(output_path) as f:
            llm_responses[output_path] = f.readlines()

    with open(outfile, "w") as f:
        for i in range(len(filenames)):
            selected_file = filenames[i]
            print(llm_responses[selected_file][i], file=f, end="")



if __name__ == "__main__":
    # script that reads a list of filenames, select lines from files in "outputs/4annot" as specified in the list. (All have the same lenght.)

    main("selected_models.txt")
