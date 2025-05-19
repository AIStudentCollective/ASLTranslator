import joblib, sklearn
from sklearn.utils.validation import check_is_fitted

mdl = joblib.load("asl_pipeline_mediapipe2.joblib")
print("Loaded type:", type(mdl))
print("scikit-learn version:", sklearn.__version__)

# Peek at the steps
if hasattr(mdl, "steps"):
    print("Pipeline steps:", [name for name, _ in mdl.steps])

# This will raise only if something inside isn't fitted
check_is_fitted(mdl)
print("✓ check_is_fitted passed")
