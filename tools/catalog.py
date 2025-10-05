# You can also use a relative path such as `ParquetDataCatalog("./catalog")`,
# for example if you're running this notebook after the data setup from the docs.
# catalog = ParquetDataCatalog("./catalog")
catalog = ParquetDataCatalog.from_env()
catalog.instruments()