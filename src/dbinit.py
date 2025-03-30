try:
    logger.info(f"Creating tables with engine: {engine}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    import traceback
    logger.error(f"Database initialization error: {e}")
    traceback.print_exc()  # 追加！スタックトレースを表示
    raise

