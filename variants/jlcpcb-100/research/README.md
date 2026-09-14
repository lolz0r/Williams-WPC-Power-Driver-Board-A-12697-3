# Research snapshots

The selected-part evidence, inventory searches, orientation records and DigiKey
pricing facts are retained here. These are dated research inputs, not stock
reservations or component qualification.

The broad catalog-search cache is stored losslessly as
[search-index.json.gz](search-index.json.gz), because its uncompressed JSON exceeds
GitHub's regular-Git file-size limit. [search-index-storage.json](search-index-storage.json)
records both sizes and SHA-256 hashes. The uncompressed local copy is ignored.

To restore the JSON when needed, run from the repository root:

```sh
gzip -dk variants/jlcpcb-100/research/search-index.json.gz
```

The committed release artifacts and their selected-part evidence retain their
existing names and hashes. The compressed cache does not change the PCB, BOM,
CPL, Gerbers or recorded simulation results.
