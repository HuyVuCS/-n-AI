import random
import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
import pandas as pd

class GeneticScheduler:
    def __init__(self, input_file, population_size=20, generations=100, mutation_rate=0.1):
        self.input_file = input_file
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.fitness_history = []

    def load_data(self):
        with open(self.input_file, "r", encoding="utf-8") as file:
            data = [line.strip().split(",") for line in file.readlines()]
        if len(data) < 2:
            raise ValueError("Không đủ dữ liệu để tạo thời khóa biểu.")
        return data

    def create_individual(self, data):
        """
        Tạo cá thể thời khóa biểu đảm bảo:
        - Mỗi buổi (sáng, chiều) có từ 3 đến 5 tiết.
        - Mỗi ngày có từ 8 đến 10 tiết.
        """
        schedule = []
        day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]
        time_slots = [f"Tiết {i + 1}" for i in range(5)]  # 5 tiết một buổi

        # Shuffle input data
        random.shuffle(data)
        day_schedule = {day: {"Sáng": [], "Chiều": []} for day in day_names}

        for entry in data:
            subject, teacher, _class = entry
            # Phân bổ lớp học vào buổi còn chỗ trống
            for day in day_names:
                for session in ["Sáng", "Chiều"]:
                    if len(day_schedule[day][session]) < 5:  # Tối đa 5 tiết mỗi buổi
                        slot = time_slots[len(day_schedule[day][session])]  # Lấy tiết học
                        day_schedule[day][session].append([day, session, slot, _class, subject, teacher])
                        break

        # Chuyển từ dictionary sang danh sách
        for day in day_names:
            for session in ["Sáng", "Chiều"]:
                schedule.extend(day_schedule[day][session])

        return schedule

    def initialize_population(self, data):
        population = []
        for _ in range(self.population_size):
            individual = self.create_individual(data)
            population.append(individual)
        return population

    def fitness(self, schedule):
        score = 0
        teacher_schedule = {}
        day_sessions = {}

        for entry in schedule:
            day, session, time, _class, subject, teacher = entry

            # Kiểm tra trùng tiết của giáo viên
            teacher_schedule.setdefault(teacher, []).append((day, session, time))
            if teacher_schedule[teacher].count((day, session, time)) > 1:
                score -= 10  # Trừ điểm nếu giáo viên bị trùng lịch

            # Đếm số tiết mỗi buổi
            day_sessions.setdefault(day, {"Sáng": 0, "Chiều": 0})[session] += 1

        # Kiểm tra số tiết mỗi buổi
        for day, sessions in day_sessions.items():
            for session, count in sessions.items():
                if count < 3:
                    score -= 10 * (3 - count)  # Trừ điểm nếu buổi có ít hơn 3 tiết
                elif count > 5:
                    score -= 10 * (count - 5)  # Trừ điểm nếu buổi có hơn 5 tiết
            total = sessions["Sáng"] + sessions["Chiều"]
            if total < 8 or total > 10:
                score -= 20  # Trừ điểm nếu tổng số tiết không hợp lệ

        return score

    def selection(self, population):
        sorted_population = sorted(population, key=self.fitness, reverse=True)
        # Nếu số cá thể quá ít, chọn tất cả
        if len(sorted_population) < 2:
            raise ValueError("Không có đủ cá thể để chọn. Hãy kiểm tra dữ liệu đầu vào hoặc thuật toán.")
        return sorted_population[:len(sorted_population)//2]



    def crossover(self, parent1, parent2):
        crossover_point = random.randint(1, len(parent1) - 1)
        child = parent1[:crossover_point] + parent2[crossover_point:]
        return child

    def mutate(self, individual):
        if random.random() < self.mutation_rate:
            for entry in individual:
                # Thay đổi giờ học
                new_time_slot = random.randint(1, 5)
                entry[2] = f"Tiết {new_time_slot}"
        return individual

    def run(self):
        data = self.load_data()
        population = self.initialize_population(data)

        for generation in range(self.generations):
            # Chọn cá thể
            selected_population = self.selection(population)
            new_population = []

            # Tạo dân số mới bằng lai ghép
            for i in range(0, len(selected_population) - 1, 2):
                parent1, parent2 = selected_population[i], selected_population[i + 1]
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                new_population.append(child)

            # Nếu dân số mới không đủ, bổ sung cá thể từ dân số cũ
            while len(new_population) < self.population_size:
                new_population.append(random.choice(selected_population))

            population = new_population

            # Ghi lại lịch sử fitness
            fitness_values = [self.fitness(ind) for ind in population]
            self.fitness_history.append({"best": max(fitness_values)})

        # Trả về cá thể tốt nhất
        best_individual = max(population, key=self.fitness)

        # Chuyển thời khóa biểu thành bảng 2D
        timetable = [["" for _ in range(6)] for _ in range(10)]  # 10 tiết (5 sáng, 5 chiều), 6 ngày
        day_indices = {"Thứ 2": 0, "Thứ 3": 1, "Thứ 4": 2, "Thứ 5": 3, "Thứ 6": 4, "Thứ 7": 5}

        for entry in best_individual:
            day, session, time, _class, subject, teacher = entry
            day_index = day_indices[day]
            time_index = int(time.split(" ")[1]) - 1  # Tính chỉ số của tiết

            # Chuyển tiết buổi chiều sang các hàng cuối (5 tiết sáng + 5 tiết chiều)
            if session == "Chiều":
                time_index += 5

            timetable[time_index][day_index] = f"{subject} - {_class} ({teacher})"

        return timetable


class TimetableApp:
    def __init__(self, master):
        self.master = master
        master.title("Quản Lý Thời Khóa Biểu")
        master.geometry("800x700")

        # Nút nhập dữ liệu
        self.btn_input = tk.Button(master, text="Nhập Dữ Liệu", command=self.show_input_dialog)
        self.btn_input.pack(pady=10)

        # Nút tạo thời khóa biểu
        self.btn_generate = tk.Button(master, text="Tạo Thời Khóa Biểu", command=self.generate_schedule)
        self.btn_generate.pack(pady=10)

        # Nút hiển thị biểu đồ fitness
        self.btn_show_chart = tk.Button(master, text="Hiển Thị Biểu Đồ Đánh Giá", command=self.show_fitness_chart)
        self.btn_show_chart.pack(pady=10)

        # Bảng thời khóa biểu
        self.table_frame = tk.Frame(master)
        self.table_frame.pack(pady=10)

        self.scheduler = None

    def show_input_dialog(self):
        input_window = tk.Toplevel(self.master)
        input_window.title("Nhập Thông Tin")
        input_window.geometry("300x250")

        # Nhãn và ô nhập
        tk.Label(input_window, text="Nhập Môn Học").pack()
        subject_input = tk.Entry(input_window)
        subject_input.pack()

        tk.Label(input_window, text="Nhập Giáo Viên").pack()
        teacher_input = tk.Entry(input_window)
        teacher_input.pack()

        tk.Label(input_window, text="Nhập Lớp Học").pack()
        class_input = tk.Entry(input_window)
        class_input.pack()

        def save_data():
            subject = subject_input.get()
            teacher = teacher_input.get()
            _class = class_input.get()

            if not all([subject, teacher, _class]):
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin.")
                return

            with open("input_data.txt", "a", encoding="utf-8") as file:
                file.write(f"{subject},{teacher},{_class}\n")
            
            messagebox.showinfo("Thành Công", "Đã lưu dữ liệu thành công.")
            input_window.destroy()

        save_button = tk.Button(input_window, text="Lưu", command=save_data)
        save_button.pack(pady=10)

    def generate_schedule(self):
        try:
            self.scheduler = GeneticScheduler("input_data.txt")
            timetable = self.scheduler.run()

            # Xóa bảng cũ nếu tồn tại
            for widget in self.table_frame.winfo_children():
                widget.destroy()

            # Tạo tiêu đề bảng
            headers = ["Buổi", "Tiết"] + ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"]

            # Tạo tiêu đề
            for j, header in enumerate(headers):
                label = tk.Label(self.table_frame, text=header, relief=tk.RIDGE, width=15, font=('Arial', 10, 'bold'))
                label.grid(row=0, column=j, sticky='nsew')

             # Phân chia sáng/chiều và hiển thị
            sessions = ["Sáng", "Chiều"]
            row_index = 1  # Bắt đầu từ hàng thứ 2

            for session in sessions:
                # Gộp ô "Buổi" cho 5 tiết liên tiếp
                label = tk.Label(self.table_frame, text=session, relief=tk.RIDGE, width=10, font=('Arial', 10, 'bold'))
                label.grid(row=row_index, column=0, rowspan=5, sticky='nsew')

                for i in range(5):  # 5 tiết mỗi buổi
                    # Cột "Tiết"
                    time_label = tk.Label(self.table_frame, text=f"Tiết {i + 1}", relief=tk.RIDGE, width=10)
                    time_label.grid(row=row_index + i, column=1, sticky='nsew')

                    # Nội dung thời khóa biểu
                    for col_index in range(6):  # 6 ngày (Thứ 2 -> Thứ 7)
                        content = timetable[row_index + i - 1][col_index] if row_index + i - 1 < len(timetable) else ""
                        label = tk.Label(self.table_frame, text=content, relief=tk.RIDGE, width=20, wraplength=150)
                        label.grid(row=row_index + i, column=col_index + 2, sticky='nsew')

                row_index += 5  # Sang buổi tiếp theo (Sáng -> Chiều)

            messagebox.showinfo("Thành Công", "Thời khóa biểu đã được tạo.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def show_fitness_chart(self):
        if not self.scheduler or not self.scheduler.fitness_history:
            messagebox.showwarning("Cảnh Báo", "Hãy tạo thời khóa biểu trước khi hiển thị biểu đồ.")
            return

        # Tách dữ liệu fitness từ lịch sử
        generations = range(1, len(self.scheduler.fitness_history) + 1)
        best_fitness = [entry["best"] for entry in self.scheduler.fitness_history]

        # Tạo biểu đồ bằng matplotlib
        plt.figure(figsize=(10, 5))
        plt.plot(generations, best_fitness, marker='o')
        plt.title('Biểu Đồ Đánh Giá Fitness Qua Các Thế Hệ')
        plt.xlabel('Thế Hệ')
        plt.ylabel('Fitness')
        plt.grid(True)
        plt.show()

def main():
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
