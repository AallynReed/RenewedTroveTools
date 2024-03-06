echo -e "Creating a python venv..."
python -m venv venv
echo -e "Installing packages..."
venv/bin/pip install -r requirements.txt > /dev/null

echo -e "Done ! Do not forget to create a simlink by doing : \e[92msudo ln -s /usr/local/lib/libmpv.so /usr/local/lib/libmpv.so.1\e[0m"
# The simlink is a temporary fix dues to a flet issue (https://github.com/flet-dev/flet/issues/2637)

# To run the app, use : `venv/bin/python app.py`
# This still requires you to manually set up your mods folder