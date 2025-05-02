# ... (existing imports) ...
import re # For case-insensitive search if needed

class ProductRepository(BaseRepository[ProductInDB, ProductCreateInternal, ProductUpdateInternal]):
    # ... (existing methods: create_indexes, get_by_sku, etc.) ...

    async def find_product_by_identifier(self, identifier: str) -> Optional[ProductInDB]:
        """
        Finds a product by SKU (exact match first) or Name (case-insensitive partial match).
        Prioritizes SKU match.
        """
        if not identifier:
            return None
        log = logger.bind(product_identifier=identifier)
        log.debug("Finding product by identifier (SKU or Name)...")

        # 1. Try exact SKU match first (common case)
        product = await self.get_by_sku(identifier)
        if product:
            log.info(f"Product found by exact SKU: {identifier}")
            return product

        # 2. Try case-insensitive Name search (more flexible for LLM)
        # Use regex for partial matching? Or exact name match? Let's do partial contains.
        # Using collation for case-insensitivity is generally better performant than regex if index supports it.
        # MongoDB Atlas often supports collation on indexes. Assumes default strength=2 (ignores case and diacritics)
        # If not using Atlas or collation isn't set up, regex is the fallback.

        # Option A: Using collation (Preferred if index supports it)
        try:
             product_by_name = await self.collection.find_one(
                 {"name": identifier},
                 collation={'locale': 'en', 'strength': 2} # Case-insensitive
             )
             if product_by_name:
                  log.info(f"Product found by exact name match (case-insensitive): {identifier}")
                  return self.model.model_validate(product_by_name)
        except Exception as e:
             log.warning(f"Could not perform name search with collation (maybe not supported?): {e}. Falling back to regex.")

        # Option B: Using regex (Fallback or if collation not available)
        # Be cautious with starting wildcard regexes (^), they can be slow without proper indexes.
        # Let's try a simple "contains" regex, case-insensitive.
        try:
            regex = re.compile(re.escape(identifier), re.IGNORECASE)
            log.debug(f"Searching name with regex: {regex}")
            product_by_name_regex = await self.collection.find_one({"name": regex})
            if product_by_name_regex:
                log.info(f"Product found by name regex match: {identifier}")
                return self.model.model_validate(product_by_name_regex)
        except Exception as e:
            log.error(f"Error performing regex search for product name '{identifier}': {e}")


        # 3. Try case-insensitive SKU match as last resort (if first exact match failed)
        try:
            product_by_sku_ci = await self.collection.find_one(
                 {"sku": identifier},
                 collation={'locale': 'en', 'strength': 2}
            )
            if product_by_sku_ci:
                log.info(f"Product found by SKU (case-insensitive): {identifier}")
                return self.model.model_validate(product_by_sku_ci)
        except Exception:
             pass # Ignore collation error here if already tried

        log.warning("Product identifier not found.")
        return None

# ... (rest of ProductRepository and OrderRepository) ...