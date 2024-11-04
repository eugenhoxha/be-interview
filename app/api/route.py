"""
This script dynamically imports and includes route modules from the 'routes' directory.
Each Python file in the 'routes' directory, except for '__init__.py', is treated as a module.
"""

import importlib
import os
import sys
import traceback
from fastapi import APIRouter
from app.logger import logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

api_router = APIRouter()
endpoints_dir = os.path.join(os.path.dirname(__file__), "routes")

for filename in os.listdir(endpoints_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        filename_clean = filename[:-3]
        module_name = f"app.api.routes.{filename_clean}"
        logger.info("Attempting to load module: %s", module_name)
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "router"):
                api_router.include_router(module.router, prefix="/organisations", tags=["organisations"])
                logger.info("Included router from module: %s", module_name)
            else:
                logger.warning("Module %s does not have a 'router' attribute.",  module_name)
        except ImportError as e:
            logger.error("ImportError when importing module %s: %s", module_name, str(e))
            logger.error(traceback.format_exc())
        except AttributeError as e:
            logger.error("AttributeError in module %s: %s", module_name, str(e))
            logger.error(traceback.format_exc())
        except SyntaxError as e:
            logger.error("SyntaxError in module %s: %s", module_name, str(e))
            logger.error(traceback.format_exc())
        except Exception as e:
            logger.error("Failed to import module %s: %s", module_name, str(e))
            logger.error(traceback.format_exc())
