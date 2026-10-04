# Matching and Score Contract

## Comparison

1. Decode the submitted JPEG and every indexed reference using the pinned CLIP image processor.
2. Obtain image feature vectors from the local CLIP vision model and normalize each vector to unit length.
3. Calculate cosine similarity between the upload vector and every indexed reference vector.
4. Select the reference with the greatest cosine similarity. Resolve exact ties deterministically by ascending normalized relative path.
5. Derive the displayed breed name from the selected image's immediate parent folder title.

The model does not query the FCI CSV or a remote service for labels or reference photographs.

## Display Score

For cosine similarity `c` in `[-1, 1]`:

```text
score = clamp(round(1 + ((c + 1) / 2) * 99), 1, 100)
```

The public result is an integer in `[1, 100]`. This is a linear display conversion of visual similarity, not a probability or calibrated measure of breed correctness. User-facing text must say so. Preserve the unrounded cosine internally for ranking; do not rank by the rounded display score.

## Accuracy Evaluation

Use a documented, deterministic sample of at least 100 labeled JPGs from the local collection. Remove every evaluation photo from the reference candidates for all predictions, while retaining non-evaluation photos from its breed folder. Count a result correct when the selected image's parent folder title matches the evaluation image's known folder title. Release acceptance requires at least 80 correct matches out of 100. Publish the evaluation sample rule, exclusions, and result; do not claim the target is achieved until the test is run.
