# notebook_helper# depencies
pip install pandas scikit-learn pyyaml networkx matplotlib

# create folder structure
mkdir data models

# one-off model training
python src/model_builder.py

# move startup.py to the path as below so that jupyter notebook can load it automatically:
cp startup.py ~/.ipython/profile_default/startup/

The newly created notebook must be parallel to the .pkl file to call the AI.