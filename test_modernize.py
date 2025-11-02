# Test Code Modernization Feature
# This file contains old Python 2 code to test the modernization system

old_python_code = '''
# Old Python 2 style code
print "Hello World"  # Python 2 print statement

# Old string formatting
name = "John"
age = 30
message = "My name is %s and I'm %d years old" % (name, age)

# Old exception handling
try:
    result = 10 / 0
except Exception, e:
    print "Error:", str(e)

# Old imports
import imp
import optparse

# Function without type hints
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total

# Using old-style classes
class OldStyleClass:
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        return self.value
'''

old_javascript_code = '''
// Old JavaScript code

// Using var instead of let/const
var name = "John";
var age = 30;

// Callback hell
fs.readFile('file1.txt', function(err, data1) {
    if (err) throw err;
    fs.readFile('file2.txt', function(err, data2) {
        if (err) throw err;
        fs.readFile('file3.txt', function(err, data3) {
            if (err) throw err;
            console.log('Done reading files');
        });
    });
});

// Old jQuery dependency
$(document).ready(function() {
    $('#button').click(function() {
        $('#content').hide();
    });
});

// Old function syntax
var add = function(a, b) {
    return a + b;
};

// No arrow functions
setTimeout(function() {
    console.log('Hello');
}, 1000);
'''

if __name__ == "__main__":
    print("=" * 60)
    print("CODE MODERNIZATION TEST SAMPLES")
    print("=" * 60)
    print("\n📝 Old Python 2 Code:")
    print("-" * 60)
    print(old_python_code)
    print("\n📝 Old JavaScript Code:")
    print("-" * 60)
    print(old_javascript_code)
    print("\n" + "=" * 60)
    print("✅ Test samples ready!")
    print("Use these code samples to test the modernization feature")
    print("in the Helix AI chat interface.")
    print("=" * 60)
