# Predicting-Code-Bloat
A Machine Learning Approach to Estimating Inlining Impact

This document contains the complete documentation for the project, explaining the problem, the technical approach, and how to run the code.

## **1\. Introduction: The Smart Compiler's Dilemma**

Imagine you're writing a cookbook. You have a tiny, common recipe you use all the time, like "how to zest a lemon." You could either write the full instructions for zesting a lemon every single time you need it, or you could just write "(see page 5 for how to zest a lemon)" and have one central recipe.

* **Writing it out every time:** This makes the main recipe longer and the whole cookbook bigger. But, a chef can read it straight through without flipping pages, making the process faster.  
* **Referring to page 5:** This keeps the main recipe short and the cookbook smaller. But, the chef has to stop, find page 5, read it, and then come back. This is slower.

This is exactly the kind of decision a **compiler** makes thousands of times when it translates your C++ code into a program your computer can run. This specific decision is called **function inlining**.

### **The Project's Big Question**

A compiler's choice to "inline" a function (copy-paste its code) can make a program faster but potentially much larger—a phenomenon known as **code bloat**. The compiler has to guess if this trade-off is worth it.  
This project asks a simple but powerful question: **Can we use machine learning to predict the exact impact of inlining on a program's size, just by looking at its source code?**  
Instead of relying on guesswork, we're building a predictive model that acts like an experienced senior developer, looking at a function and saying, "I predict that inlining this function will increase the final program size by about 3.5%." This project is a practical application of machine learning to a classic compiler problem.

## **2\. The Problem in Detail: Compilers and Code Bloat**

To understand our project, let's quickly break down two key concepts: what a compiler does and what "function inlining" really is.

### **What is a Compiler?**

A compiler is a special program that acts as a translator. It takes the human-readable source code you write (in our case, C++) and translates it into machine code (a binary file) that your computer's processor can execute directly.  
During this translation, the compiler doesn't just do a word-for-word conversion. It's incredibly smart and performs many **optimizations** to make the final program run as fast and efficiently as possible. One of the most common and important optimizations is function inlining.

### **What is Function Inlining?**

Let's look at a simple C++ example.  
**Before Inlining (Normal Code):**  

```cpp
// A simple function to calculate the square  
int square(int x) {  
    return x \* x;  
}

int main() {  
    int result \= square(5); // The CPU has to jump to the 'square' function  
    return 0;  
}
```

When this code runs, the main function "calls" the square function. This involves saving its current state, jumping to the square function's location in memory, executing its code, and then returning. This jump has a small time cost, known as **call overhead**.  
**After Inlining (Compiler Optimization):**  
The compiler might decide to "inline" the square function. It replaces the function call directly with the function's body:
```cpp
int main() {  
    int result \= 5 \* 5; // The compiler copy-pasted the function's code\!  
    return 0;  
}
```

**The Trade-Off:**

* **Pro:** The program is now faster because there's no call overhead. The CPU can execute the code in a straight line.  
* **Con:** If the square function was very large and was called from 100 different places, its code would be duplicated 100 times. This would make the final binary file much larger, causing **code bloat**.

Our project's goal is to predict this "Con." We want to build a model that can look at any function and predict the percentage increase in binary size if it were to be inlined.

## **3\. Our Approach: A 4-Step Plan**

To predict the impact of inlining, we'll use a standard machine learning pipeline. We need to create a dataset of examples that a model can learn from. Our approach is broken down into four main steps, each handled by a dedicated script.

### **Step 1: Generate a C++ Codebase (generate\_code.py)**

A machine learning model needs a lot of data to learn. We can't write thousands of C++ functions by hand, so we automate it. This script procedurally generates hundreds of .cpp files, each containing functions with varying levels of complexity, size, and structure. This gives us a large, diverse "laboratory" of code to analyze.

### **Step 2: Measure the Impact (generate\_data.py)**

This is where we create the "answer key" for our model. For every single function generated in Step 1, this script does the following:

1. Compiles the code while forcing the target function **not** to be inlined (\_\_attribute\_\_((noinline))).  
2. Measures the size of the resulting object file (.o).  
3. Compiles the code again, this time forcing the function to be inlined (\_\_attribute\_\_((always\_inline))).  
4. Measures the new object file size.  
5. Calculates the percentage difference and saves it to size\_impact.csv.

This file contains the "ground truth" that our model will try to predict.

### **Step 3: Find Clues in the Code (extract\_features.py)**

A model can't read code directly; it needs numerical clues, or **features**. This script parses the C++ code and, for each function, extracts static features like:

* **cyclomatic\_complexity**: How many decision points (if, for, while) are in the function?  
* **token\_count**: How many "words" or symbols make up the function?  
* **parameter\_count**: How many arguments does it take?  
* And several others.

This script uses a compiler tool called libclang to understand the code's structure, known as an **Abstract Syntax Tree (AST)**. These features are saved in features.csv.

### **Step 4: Train the Predictive Model (train\_model.py)**

This is the final step. The script:

1. Merges our two datasets (size\_impact.csv and features.csv).  
2. Splits the data into a training set and a testing set.  
3. Trains a **LightGBM** regression model on the training data. The model learns the complex relationships between the code's features and its eventual impact on binary size.  
4. Evaluates the model on the unseen testing data to see how accurate its predictions are.  
5. Saves the trained model to a file for future use.

## **4\. How to Run the Project: A Step-by-Step Guide**

This guide will walk you through setting up and running the entire project pipeline from your terminal.

### **Prerequisites**

Before you begin, make sure you have the following tools installed on your system.

1. **A C++ Compiler:** This project uses clang++. On macOS, it's included with Xcode Command Line Tools.  
2. **Python 3:** The scripts are written in Python (version 3.8+ recommended).  
3. **Pip:** Python's package installer, which usually comes with Python.  
4. **Homebrew (macOS only):** A package manager for macOS, used to install system dependencies.

### **Setup Instructions**

1. **Clone the Repository:**
    ```commandline
   git clone https://github.com/ashishh2/Predicting-Code-Bloat.git 
   cd Predicting-Code-Bloat
   ```

2. Install System Dependencies (macOS):  
   These libraries are required for the lightgbm and libclang Python packages to work correctly.
    ```zsh
   brew install libomp  
   brew install llvm
    ```

3. Create a Python Virtual Environment:  
   This isolates the project's dependencies from your system's Python.  
    ```zsh
   python3 -m venv .venv  
   source .venv/bin/activate
    ```

4. Install Python Packages:  
   (Note: You will need to create a requirements.txt file containing pandas, scikit-learn, lightgbm, joblib, and libclang).  
   ```zsh
    pip install -r requirements.txt
   ```

### **Running the Full Pipeline**

Execute the following scripts from the project's root directory **in this specific order**.

1. Generate C++ Source Code:  
   This will create the src\_generated/ directory with hundreds of .cpp files.
   ```zsh
   python scripts/generate\_code.py
   ```

2. Generate Size Impact Data:  
   This is the longest step, as it compiles each function twice. It will produce the data/size\_impact.csv file.
   ```zsh
   python scripts/generate\_data.py
   ```

3. Extract Static Features:  
   This script parses the generated C++ code and creates the data/features.csv file.
   ```zsh
   python scripts/extract\_features.py
   ```

4. Train and Evaluate the Model:  
   This is the final step. It loads the generated data, trains the model, and saves the final product to output/inlining\_impact\_model\_scaled.joblib.
   ```zsh
   python scripts/train\_model.py
   ```

After running these steps, you will have successfully replicated the entire project and trained your own predictive model.