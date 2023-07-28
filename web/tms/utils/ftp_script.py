import ftplib
import os
import datetime
import pandas as pd

# from tms.models import Tenement


def scrape_tenement_ftp():
    """Populates the database from updated files within the FTP server

    Returns
    -------
        success : bool
            True if the scraping was successful, false otherwise
    """
    # Get Credentials from environment variables
    url = os.environ.get('FTP_URL', "ftp.example.com")
    username = os.environ.get('FTP_USERNAME', "username")
    password = os.environ.get('FTP_PASSWORD', "password")

    # Connect to the FTP server
    ftp = ftplib.FTP(url)
    ftp.login(username, password)

    # List the files on the FTP server
    files = ftp.nlst()

    # Get the timestamp of the last time the script ran
    try:
        with open("last_run.txt", "r") as f:
            last_run = f.read()
        last_run = datetime.datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S.%f")
    except FileNotFoundError:
        last_run = datetime.datetime(1970, 1, 1)

    # Iterate through the files on the FTP server
    for file in files:
        # Get the timestamp of the file, MDTM is the datetime of the file when it was uploaded
        timestamp = ftp.sendcmd("MDTM " + file).split()[1]
        timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")

        # Check if the file was modified since the last time the script ran
        if timestamp <= last_run:
            continue

        # Download the file
        with open(file, "wb") as f:
            ftp.retrbinary("RETR " + file, f.write)

        # Read and parse the data from the file using pandas
        df = pd.read_csv(file)

        # Iterate through the rows of the DataFrame
        for index, row in df.iterrows():
            permit_type = row['PermitType']
            permit_number = row['PermitNumber']

            # Map the other fields we need to build the tenement model
            data_mapped = {
                # 'permit_status': row['PermitStatus'],
                # ...
            }

            # Create or update a new Tenement. If a permit with the type
            # and number don't exist, it is created, otherwise update
            # TODO: Uncomment this component
            # tenement, created = Tenement.objects.update_or_create(
            #     permit_type=permit_type,
            #     permit_number=permit_number,
            #     defaults=data_mapped
            # )

            # Handle other objects that need to be created
            # Blocks
            # SubBlocks
            # ...

            # Print results to console
            # print("[FTP][%s:%s %s]" % ("CREATED" if created else "UPDATED", permit_type, permit_number))


    # Save the current timestamp to a file
    with open("last_run.txt", "w") as f:
        f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

    # Close the FTP connection
    ftp.quit()

    return True