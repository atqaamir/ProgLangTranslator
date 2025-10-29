#include <iostream>
#include <string>
using namespace std;

class Animal {
public:
    string name;
    Animal(string n) : name(n) {}
    virtual void speak() {
        cout << name << " makes a sound" << endl;
    }
};

class Dog : public Animal {
public:
    Dog(string n) : Animal(n) {}
    void speak() override {
        cout << name << " barks!" << endl;
    }
};

int main() {
    Animal a("Generic");
    Dog d("Rex");
    a.speak();
    d.speak();
    return 0;
}


