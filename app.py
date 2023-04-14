import atoti as tt
from flask import Flask, request

# Initialize the Flask app
app = Flask(__name__)

# Initialize the Atoti session
session = tt.Session(
    port=9090,
    user_content_storage="./content",
)


# Define the route to handle the dataset upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the uploaded file from the request
    file = request.files['file']

    # Read the uploaded file as a Pandas DataFrame
    df = pd.read_csv(file)

    # Create the cube using the DataFrame
    cube = session.create_cube(df)

    # Link the cube to the session
    session.link()

    # Return a message indicating success
    return 'Dataset uploaded successfully!'


if __name__ == '__main__':
    app.run()
