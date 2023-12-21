#pragma once
#include <assert.h>
#include <string>
#include <fstream>
#include <vector>

using namespace std;


class FileManager
{
public:
	FileManager(const string& _sequenceListPath, const string& _maskListPath);

	string getSequencePath();
	string getMaskPath();

	bool eof();

private:
	bool _eof;
	
	string sequenceListPath;
	string maskListPath;

	ifstream sequenceListHandler;
	ifstream maskListHandler;

	vector<string> sequencePaths;
	vector<string> maskPaths;

	vector<string>::iterator sequenceIterator;
	vector<string>::iterator maskIterator;

	uint32_t sequenceCount;
	uint32_t maskCount;


};

