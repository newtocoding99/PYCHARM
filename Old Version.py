

# !/usr/bin/env python3

import tkinter as tk
import datetime as dt
import csv
from pathlib import Path
import PIL.Image
import PIL.ImageDraw
import PIL.ImageTk



MAX_HEIGHT = 500
b = 2
new_height = MAX_HEIGHT * b


IMAGES_PATH = Path("/Users/poojapatel/Desktop/Research/Images")
CSV_LABELS_KEY = "New Labels"
CSV_IMAGE_NAME = "FolderNum_SeriesNum"
CSV_CORRECT_BOUNDING_BOX = "ground_truth_bbox"


# height of the window (dimensions of the image)
class App(tk.Frame):

    def __init__(self, set_numbers_to_rows, master=None):
        super().__init__(master)  # python3 style
        self.set_numbers_to_rows = set_numbers_to_rows
        self.set_numbers = iter(self.set_numbers_to_rows.keys())

        self.rect_num = 0
        self.loaded_images = dict()
        self.loaded_boxes = dict()
        # this dictionary will keep track of all the boxes drawn on the images
        self.clickStatus = tk.StringVar()
        self.current_drag_box = []
        # currently dragging Box
        self.filenames = []
        self.current_index = 0
        self.image_name = None
        self.master.title("Slideshow")
        self.drawing_enabled = True
        frame = tk.Frame(self)

        # This is everything for the button placement
        top_frame = tk.Frame(self)
        bottom_frame = tk.Frame(self)
        image_frame = tk.Frame(self)
        top_frame.pack(side="top", fill="x")
        bottom_frame.pack(side="bottom", fill="x")
        image_frame.pack(side="top", fill="both", expand=True)

        exit_button = tk.Button(bottom_frame, text="       Exit        ", height=2, command=self.quit)
        exit_button.pack(side="right")
        previous_button = tk.Button(top_frame, text="Previous Slice", height=2, command=self.prev_image)
        previous_button.pack(side="left")
        next_button = tk.Button(top_frame, text="  Next Slice  ", height=2, command=self.next_image)
        next_button.pack(side="left")
        clear_button = tk.Button(top_frame, text="  Clear  ", height=2, command=self.clear_rect)
        clear_button.pack(side="left")
        _disable_drawing_button = tk.Button(top_frame, text="       Draw box/Click Box      ", height=2, command=self._toggle_drawing)
        _disable_drawing_button.pack(side="left")
        next_set_button = tk.Button(top_frame, text="       Next Set       ", height=2, command=lambda:[self.get_next_image_set(), self.timer()])
        next_set_button.pack(side="right")

        self.image_name = tk.Label(bottom_frame, text="", height=2, width=120, fg="blue")
        self.image_name.pack(side="bottom")



        frame.pack(side=tk.TOP, fill=tk.BOTH)
        self.canvas = tk.Canvas(self)

        # to add left and right keyboard clicks
        self.canvas.bind('<Right>', self.next_image)
        self.canvas.bind('<Left>', self.prev_image)
        self.canvas.focus_set()
        # frame.focus_set()

        # in order to support mouse drag to draw a box
        self.canvas.bind("<ButtonPress-1>", self.mouse_down_evt)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up_evt)
        self.canvas.bind("<Motion>", self.mouse_move_evt)

        self.dragging = False
        # when you click button, it opens event of clicked_evt
        self.canvas.pack()
        # self.pack() # by tradition this goes in the calling function, not here
        self.current_image_index = 0
        self.image_set_rows = []  # Immediately overwritten by self.get_next_image_set()
        self.get_next_image_set()



        self.current_time = dt.datetime.today()
        self.load_image()



    def get_current_image_row(self):
        return self.image_set_rows[self.current_image_index]


    def get_next_image_set(self):
        if len(self.image_set_rows) != 0:
            self.save_to_csv()
            self.loaded_boxes = {}
        try:
            set_number = next(self.set_numbers)
            rows = self.set_numbers_to_rows[set_number]

        except StopIteration:
            return self.image_set_rows

        self.image_set_rows = rows
        self.load_image()


    def prev_image(self, event=None):
        self.current_image_index = (self.current_image_index - 1) % len(self.image_set_rows)
        self.load_image()
        # self.master.bind('<Left>', self.prev_image)

        self.current_index = self.current_index - 1
        self.image_name.config(text=self.filenames[self.current_index % len(self.filenames)][:-4])

    def next_image(self, event=None):
        self.current_image_index = (self.current_image_index + 1) % len(self.image_set_rows)
        self.load_image()
        # self.master.bind('<Right>', self.next_image)

        self.current_index = self.current_index + 1
        self.image_name.config(text=self.filenames[self.current_index % len(self.filenames)][:-4])

    def clear_rect(self):
        image_row = self.get_current_image_row()
        file_name = image_row[CSV_IMAGE_NAME]
        self.loaded_boxes[file_name] = []
        self.load_image()

    def timer(self):
        now = dt.datetime.today()
        time_elapsed = now - self.current_time
        print(time_elapsed)
        self.current_time = now


        current_index = (self.current_index - 1)
        #self.image_name.config(text=self.filenames[self.current_index % len(self.filenames)][:-4])
        previous_file_name = current_index % len(self.filenames)
        print(f"{previous_file_name}")

        #file_name = (self.get_current_image_row())[CSV_IMAGE_NAME]
        #with open('Example.csv', 'a') as outputCSV:
            #writer = csv.writer(outputCSV)
            #writer.writerow({f"{file_name}, {time_elapsed}"})


    def _toggle_drawing(self):
        if self.drawing_enabled:
            self.drawing_enabled = False
            self.canvas.bind("<Button-1>", self.clicked_evt)
            self.canvas.delete('drag_box')
            # to ensure no repeats

        else:
            self.drawing_enabled = True
            self.canvas.bind("<ButtonPress-1>", self.mouse_down_evt)
            self.canvas.bind("<ButtonRelease-1>", self.mouse_up_evt)
            self.canvas.bind('<Motion>', self.mouse_move_evt)
            # to ensure no repeats
            #self.canvas.delete("box")
            # got rid of this so that it stays after pressing toggle button again

    def mouse_down_evt(self, evt):
        # record the starting position of the drag and note that dragging started
        self.dragging = True
        x, y = evt.x, evt.y
        self.current_drag_box.append([(x, y), None])


    def mouse_up_evt(self, evt):
        if self.dragging:
            # if the dragging was happening then we note that it ended and log the final
            # box coordinates
            self.dragging = False
            x, y = evt.x, evt.y
            last = self.current_drag_box[-1]
            last[1] = (x, y)

            file_name = self.get_current_image_row()[CSV_IMAGE_NAME]
            self.loaded_boxes[file_name] = self.current_drag_box.copy()


    def save_to_csv(self):
        with open("Example.csv", "a") as outputCSV, \
                open("Example.csv", 'w', newline='') as write_obj:
            writer = csv.writer(outputCSV)
            reader = csv.reader(write_obj)
            for file_name in self.loaded_boxes.keys():
                writer.writerow({f"{file_name}, {self.loaded_boxes[file_name]}"})


    def mouse_move_evt(self, evt):
        if self.dragging:
            x, y = evt.x, evt.y
            last = self.current_drag_box[-1]
            last[1] = (x, y)
            self.show_drag_box()

    def show_drag_box(self):
        # This function will draw a box on the canvas using the saved coordinates
        index = 0
        for r in self.current_drag_box:
            (l, t), (r, b) = r
            tag = "drag_box_" + str(index)
            self.canvas.delete(tag)
            self.canvas.create_rectangle(l, t, r, b, tag=tag, outline="magenta", width=2)
            self.canvas.pack(expand=1)
            index += 1

    def clicked_evt(self, evt):
        x, y = evt.x, evt.y
        image_row = self.get_current_image_row()
        file_name = image_row[CSV_IMAGE_NAME]
        image_data = self.loaded_images[file_name]
        # self.canvas.delete("box")
        # this is for all the correct coordinates in correct_flip_bbox to have a box display upon click of the perimeter
        for shape in image_data["shapes"]:
            print("ground_truth_bbox", f"x: {x}, y: {y}")
            b = 2
            l = int(shape["left"]) * b
            t = int(shape["top"]) * b
            r = int(shape["right"]) * b
            b = int(shape["bottom"]) * b

            left_or_right_line = ((l - 4) <= x <= (l + 4) or (r - 4) <= x <= (r + 4)) and (t - 4) <= y <= (b + 4)
            bottom_or_top_line = ((t - 4) <= y <= (t + 4) or (b - 4) <= y <= (b + 4)) and (l - 4) <= x <= (r + 4)
            if left_or_right_line or bottom_or_top_line:
                self.canvas.create_rectangle(l, t, r, b, tag="box", outline="magenta", )
                self.canvas.pack(expand=1)

                file_name = self.get_current_image_row()[CSV_IMAGE_NAME]
                self.loaded_boxes[file_name] = self.current_drag_box.copy()
                with open('Example.csv', 'a') as outputCSV:
                    writer = csv.writer(outputCSV)
                    writer.writerow({f"{file_name}, x: {x}, y: {y}"})
                    
        # this is for all the wrong coordinates in wrong_flip_bbox to have a box display upon click of the perimeter
        predictions_bbox = image_row['predictions_bbox']
        # print("wrong_flip_bbox", f"x: {x}, y: {y}")
        if predictions_bbox is not None and predictions_bbox != '':
            for item in predictions_bbox.split(":"):
                coordinates = [int(p) for p in item.split(",")]
                if len(coordinates) >= 4:
                    b = 2
                    l = coordinates[0] * b
                    t = coordinates[1] * b
                    r = coordinates[2] * b
                    b = coordinates[3] * b

                    left_or_right_line = ((l - 4) <= x <= (l + 4) or (r - 4) <= x <= (r + 4)) and (t - 4) <= y <= (b + 4)
                    bottom_or_top_line = ((t - 4) <= y <= (t + 4) or (b - 4) <= y <= (b + 4)) and (l - 4) <= x <= (r + 4)
                    if left_or_right_line or bottom_or_top_line:
                        self.canvas.create_rectangle(l, t, r, b, tag="box", outline="magenta", )
                        self.canvas.pack(expand=1)

                        file_name = self.get_current_image_row()[CSV_IMAGE_NAME]
                        self.loaded_boxes[file_name] = self.current_drag_box.copy()
                        with open('Example.csv', 'a') as outputCSV:
                            writer = csv.writer(outputCSV)
                            writer.writerow({f"{file_name}, x: {x}, y: {y}"})

                        break




    def load_image(self):
        image_row = self.get_current_image_row()
        file_name = image_row[CSV_IMAGE_NAME]
        self.image_name.config(text=file_name[:-4])

        if file_name not in self.loaded_images:
            input_image = PIL.Image.open(IMAGES_PATH / file_name)
            self.filenames.append(file_name)
            ratio = new_height / input_image.height
            # ratio divided by existing height -> to get constant amount
            height, width = int(input_image.height * ratio), int(input_image.width * ratio)
            # calculate the new h and w and then resize next
            self.canvas.config(width=width, height=height)
            input_image = input_image.resize((width, height))

            if input_image.mode == "1":
                display_image = PIL.ImageTk.BitmapImage(input_image, foreground="white")
            else:
                display_image = PIL.ImageTk.PhotoImage(input_image)

            image_data = self.loaded_images.setdefault(file_name, dict())
            image_data["image"] = display_image
            image_data["shapes"] = get_shapes(image_row[CSV_CORRECT_BOUNDING_BOX])

        # for next and previous so it loads the same image and doesn't repeat calculations
        display_image = self.loaded_images[file_name]["image"]
        self.canvas.create_image(0, 0, anchor=tk.NW, image=display_image)

        self.current_drag_box = self.loaded_boxes[file_name] if file_name in self.loaded_boxes else []
        self.show_drag_box()


def get_shapes(bounding_box):
    data = bounding_box.split(',')
    box = dict()
    box['left'] = int(data[0])
    box['top'] = int(data[1])
    box['right'] = int(data[2])
    box['bottom'] = int(data[3])
    # box["is_target"] = True
    return [box]

def read_csv_rows(csv_path):
    with open(csv_path, newline="", mode="r") as csv_file:
        # use csv module to read in lines as dict where keys are the headers
        reader = csv.DictReader(csv_file)
        rows = [row for row in reader]  # probably not the best way of reading the rows
        return rows

def get_image_set(row):
    specific_foldernum_seriesnum = row[CSV_IMAGE_NAME]
    # Splits the name on the "_" and then takes the first two values and then joins them back together with an _
    image_set = "_".join(specific_foldernum_seriesnum.split("_")[:2])
    # Gets everything before the second '_'

    return image_set
    # new name of image where it is defined by slice number

def get_set_numbers_to_rows(rows):
    set_number_to_rows = {}
    # goes over each row and obtains the image_Set name and builds a dict using that name as the key along with the row
    # if the file name already appears, it appends the additional rows
    # set.default means if the value in image_set does not already exist, use [] and then append the row
    for row in rows:
        # for each row we get the first two numbers in the file name (image set)
        image_set = get_image_set(row)
        # then we append the row to a list
        set_number_to_rows.setdefault(image_set, []).append(row)
    return set_number_to_rows


def load_set_numbers_to_rows(csv_path):
    rows = read_csv_rows(csv_path)
    set_number_to_rows = get_set_numbers_to_rows(rows)
    return set_number_to_rows


if __name__ == "__main__":
    set_number_to_rows = load_set_numbers_to_rows('/Users/poojapatel/Desktop/Research/DatasetNIH.csv')
    app = App(set_number_to_rows)
    app.pack()
    app.mainloop()
