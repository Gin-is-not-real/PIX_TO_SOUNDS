# Pix to Sounds
Read an image as sounds.

A wx frame and classes for load an image, edit it, and read it as an inverted frequency spectrum with a pyo oscillator.

## Libraries/modules
- wx
- matplotlib
- PIL
- numpy
- pyo
- time
- os, inspect

## Fonctionnement
The image is read, line by line or column by column depending on the chosen direction, as a frequency spectrum where each series of pixels represents the amplitude level of the corresponding frequency.

The number of frequencies of the oscillator is defined by the size of the image (number of lines or columns), and the duration and the number of reading steps are defined by the number of lines or columns depending on the reading_direction and the time sleep parameter in the read() method of the Player

Also, images that are too large will take a long time to process and will contain a lot of unwanted harmonics. 

>> for an image with 30 lines and 20 columns, the oscillator will be composed of: 
    - 30 frequencies whose amplitudes will vary 20 times if the reading_direction is horizontal 
    - 20 frequencies that will vary 30 times if is vertical.

*The image is resized to 1000x1000 when it is loaded in the ImageData method init_data_from_path. You can edit max image size values inside if necessary. (in fact, 1000 frequencies is already a high value)


The frequencies values of the oscillator are defined by the fondamental frequency (first oscillator frequency), the number of frequences and the gap selected 

>> For a first frequency of 30Hz, and a gap of 5, the oscillator frequencies will be 30Hz, 35Hz, 40Hz... 


## Architecture
ImageData and ReaderData are instancied as globals objects for store and manipulate the differents state of data. 
(...)

## Image controls
- black and white lvls limits
- reverse colors
- flip horizontaly/verticaly
- rotate

## Reader controls
- reading direction
- reading index (for soon display current data)

## Player controls
- play/pause
- stop
- fondamental frequency
- frequency gap