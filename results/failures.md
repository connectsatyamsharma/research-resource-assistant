# Failure analysis (hybrid, nDCG@5 < 0.6)

- **H01** `tomato blight detection` -> P@5=0.00, nDCG=0.00
- **H02** `self-driving vehicle perception` -> P@5=0.40, nDCG=0.44
- **H04** `recognise hate speech on social media` -> P@5=0.00, nDCG=0.00

# Abstention outcomes (queries with no gold resource)

- I03 `data` [keyword] abstained=True status=no_match
- I03 `data` [semantic] abstained=True status=too_vague
- I03 `data` [hybrid] abstained=True status=too_vague
- I04 `blockchain voting system` [keyword] abstained=True status=no_match
- I04 `blockchain voting system` [semantic] abstained=True status=no_match
- I04 `blockchain voting system` [hybrid] abstained=True status=no_match
- I05 `` [keyword] abstained=True status=empty_query
- I05 `` [semantic] abstained=True status=empty_query
- I05 `` [hybrid] abstained=True status=empty_query