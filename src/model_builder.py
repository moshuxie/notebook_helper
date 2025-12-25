import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# 1. Load Data
try:
    df = pd.read_csv("../data/steward_data.csv")
    print(f"Loaded {len(df)} training examples.")
except FileNotFoundError:
    print("Error: Please create 'steward_data.csv' first!")
    exit()

# 2. Train Model
# ngram_range=(1, 5): 
# This is crucial. It allows the model to see "name is not defined" 
# as a specific phrase, ensuring VARIABLE_ERROR is detected correctly 
# even amidst complex DevOps logs.
model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 5), stop_words='english'), 
    MultinomialNB(alpha=0.1) # alpha=0.1 helps with features that appear rarely
)

print("Training model...")
model.fit(df['text'], df['category'])

# 3. Create Maps
advice_map = pd.Series(df.solution.values, index=df.category).to_dict()
devops_scope_map = {k: bool(v) for k, v in pd.Series(df.is_devops.values, index=df.category).to_dict().items()}

# 4. Save
brain_package = {
    "model": model,
    "advice_map": advice_map,
    "devops_scope_map": devops_scope_map
}
joblib.dump(brain_package, "../models/it_steward_brain.pkl")
print("✅ Brain trained successfully.")
print("   - Includes GCP, K8S, Spark, and Docker patterns.")
print("   - Variable/Typo detection logic reinforced.")

