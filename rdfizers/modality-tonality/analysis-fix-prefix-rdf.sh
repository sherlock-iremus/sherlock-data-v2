cd out/ttl/modality-tonality/
echo "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n$(cat analysis.ttl)" > analysis.ttl
cd -