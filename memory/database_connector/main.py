@@ .. @@
                 execution_time_ms=execution_time_ms
 
             
-        except Exception as e:
-            execution_time_ms = int((time.monotonic() - start_time) * 1000)
-            logger.error(f"Database operation failed: {str(e)}")
-            
-            # Log the error
-            await self._log_database_operation(
-                operation_type=inputs.get('operation_type', 'unknown'),
-                error=str(e)
-
-            
-            return AgentResult(
-                status=AgentStatus.FAILED,
-                data={
-                    "error": f"Database operation failed: {str(e)}",
-                    "error_type": type(e).__name__,
-                    "operation_type": inputs.get('operation_type')
-                })
-                # Corrected closing parenthesis
-                },
-                execution_time_ms=execution_time_ms
-
+        except Exception as e:
+            execution_time_ms = int((time.monotonic() - start_time) * 1000)
+            logger.error(f"Database operation failed: {str(e)}")
+            
+            # Log the error
+            await self._log_database_operation(
+                operation_type=inputs.get('operation_type', 'unknown'),
+                error=str(e)
+            )
+            
+            return AgentResult(
+                status=AgentStatus.FAILED,
+                data={
+                    "error": f"Database operation failed: {str(e)}",
+                    "error_type": type(e).__name__,
+                    "operation_type": inputs.get('operation_type')
+                },
+                execution_time_ms=execution_time_ms
+            )
 
     def __del__(self):
         """Clean up database connections on agent destruction."""