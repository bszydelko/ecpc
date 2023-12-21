#include "FileManager.h"

FileManager::FileManager(const string& _sequenceListPath, const string& _maskListPath)
{
	sequenceCount = 0;
	maskCount = 0;

	sequenceListPath = _sequenceListPath;
	maskListPath = _maskListPath;

	sequenceListHandler.open(sequenceListPath, ios::in);
	maskListHandler.open(maskListPath, ios::in);

	assert(sequenceListHandler.is_open() == true);
	assert(maskListHandler.is_open() == true);

	string data = "";
	while (!sequenceListHandler.eof())
	{
		sequenceListHandler >> data;
		sequencePaths.push_back(data);
		sequenceCount++;
	}
	assert(sequencePaths.empty() == false);

	while (!maskListHandler.eof())
	{
		maskListHandler >> data;
		maskPaths.push_back(data);
		maskCount++;
	}
	assert(maskPaths.empty() == false);

	assert(sequenceCount == maskCount);
	
	sequenceIterator = sequencePaths.begin();
	maskIterator = maskPaths.begin();

	_eof = false;
}

string FileManager::getSequencePath()
{
	if (sequenceIterator == sequencePaths.end())
		_eof = true;
	return string(*sequenceIterator++);
}

string FileManager::getMaskPath()
{
	if (maskIterator == maskPaths.end())
		_eof = true;
	return string(*maskIterator++);
}

bool FileManager::eof()
{
	return _eof;
}
