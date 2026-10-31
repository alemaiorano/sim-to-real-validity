PYTHON ?= python3
SOURCE_DATE_EPOCH ?= 1793404800
export SOURCE_DATE_EPOCH

.PHONY: verify assets reproduce arxiv test checksums

verify:
	sha256sum -c REPLICATION_SHA256SUMS

assets:
	$(PYTHON) scripts/generate_paper_variables.py
	$(PYTHON) scripts/generate_validity_table.py
	$(PYTHON) scripts/generate_replication_table.py
	$(PYTHON) scripts/generate_crossmodel_table.py
	$(PYTHON) scripts/generate_pilot_table.py
	$(PYTHON) scripts/generate_h5_table.py
	$(PYTHON) scripts/generate_supplementary_tables.py
	$(PYTHON) scripts/generate_reanalysis_assets.py
	$(PYTHON) scripts/generate_recollection_assets.py
	$(PYTHON) scripts/generate_window_sensitivity_assets.py

reproduce: assets
	cd latex && pdflatex -halt-on-error -interaction=nonstopmode main
	cd latex && bibtex main
	cd latex && pdflatex -halt-on-error -interaction=nonstopmode main
	cd latex && pdflatex -halt-on-error -interaction=nonstopmode main
	$(PYTHON) scripts/build_arxiv_package.py

arxiv: reproduce

test:
	$(PYTHON) -B -m unittest discover -s tests -v

# Stage intended payload changes before regenerating the catalog.
checksums:
	$(PYTHON) scripts/build_replication_checksums.py
