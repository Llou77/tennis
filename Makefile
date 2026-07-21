.PHONY: setup test ingest features train predict value news pipeline
setup:      ; python -m pip install -e ".[dev]"
test:       ; python -m pytest -q
ingest:     ; python -m tennisbet ingest
features:   ; python -m tennisbet features
train:      ; python -m tennisbet train
predict:    ; python -m tennisbet predict
value:      ; python -m tennisbet value
news:       ; python -m tennisbet news
pipeline:   ; python -m tennisbet pipeline
