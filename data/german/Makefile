

# SAUERKRAUT = $(patsubst mistral-answers.%,german-sauerkraut-annotation.%,$(wildcard mistral-answers*.jsonl))
SAUERKRAUT = $(patsubst %.jsonl,%.old,$(wildcard german-sauerkraut*.jsonl))

sauerkraut: ${SAUERKRAUT}

select: german_selected_outputs.jsonl



# ${SAUERKRAUT}: german-sauerkraut-annotation.%: mistral-answers.%
# 	sed 's/model_output/output_text/' < $< > $@

${SAUERKRAUT}: %.old: %.jsonl
	mv $< $@
	sed 's/model_output/output_text/' < $@ > $<
	touch $@

german_selected_outputs.jsonl:
	python3 selecting_outputs.py



