from robot.api import ExecutionResult, ResultVisitor
import argparse
import os
from sqlalchemy import create_engine, Column, ForeignKey, Sequence, String, Integer, Float, JSON, DateTime, func, text
from sqlalchemy.orm import sessionmaker, declarative_base


Base = declarative_base()
engine = create_engine(f"postgresql://{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_DATABASE']}")

class TestRun(Base):
    __tablename__ = "testrun_results"
    id = Column(Integer, Sequence('testrun_id_seq'), primary_key=True)
    testsuite = Column("testrun", String)
    passed = Column("passed", Integer)
    failed = Column("failed", Integer)
    skipped = Column("skipped", Integer)
    total = Column("total", Integer)
    elapsedtime = Column("elapsedtime", Float)
    starttime = Column("starttime", DateTime)
    endtime = Column("endtime", DateTime)

    def __init__(self, testsuite, passed, failed, skipped, total, elapsedtime, starttime, endtime):
        self.testsuite = testsuite
        self.passed = passed
        self.failed = failed
        self.skipped = skipped
        self.total = total
        self.elapsedtime = elapsedtime
        self.starttime = starttime
        self.endtime = endtime

class TestSuite(Base):
    __tablename__ = "suite_results"
    id = Column(Integer, Sequence('testsuite_id_seq'), primary_key=True)
    testrunid = Column(Integer, ForeignKey("testrun_results.id"))
    testsuite = Column("testsuite", String)
    passed = Column("passed", Integer)
    failed = Column("failed", Integer)
    skipped = Column("skipped", Integer)
    total = Column("total", Integer)
    elapsedtime = Column("elapsedtime", Float)
    starttime = Column("starttime", DateTime)
    endtime = Column("endtime", DateTime)

    def __init__(self, testrunid, testsuite, passed, failed, skipped, total, elapsedtime, starttime, endtime):
        self.testrunid = testrunid
        self.testsuite = testsuite
        self.passed = passed
        self.failed = failed
        self.skipped = skipped
        self.total = total
        self.elapsedtime = elapsedtime
        self.starttime = starttime
        self.endtime = endtime

class TestResults(Base):
    __tablename__ = "test_results"
    id = Column(Integer, Sequence('testresult_id_seq'), primary_key=True)
    testsuiteid = Column(Integer, ForeignKey("suite_results.id"))
    testcase = Column("testcase", String)
    status = Column("status", String)
    elapsedtime = Column("elapsedtime", Float)
    starttime = Column("starttime", DateTime)
    endtime = Column("endtime", DateTime)

    def __init__(self, testsuiteid, testcase, status, elapsedtime, starttime, endtime):
        self.testsuiteid = testsuiteid
        self.testcase = testcase
        self.status = status
        self.elapsedtime = elapsedtime
        self.starttime = starttime
        self.endtime = endtime

class TestResultsJSON(Base):
    __tablename__ = "test_results_json"
    id = Column(Integer, Sequence('testresultjson_id_seq'), primary_key=True)
    testresultid = Column(Integer, ForeignKey("test_results.id"))
    json = Column(JSON)


    def __init__(self, testresultid, json ):
        self.testresultid = testresultid
        self.json = json

class SuitesWithTestsVisitor(ResultVisitor):
    def __init__(self):
        self.suites_with_tests = []

    def start_suite(self, suite):
        if suite.tests:
            self.suites_with_tests.append(suite)
 
def upload_results(input):
    result = ExecutionResult(input)
    stats = result.statistics
    suite_visitor = SuitesWithTestsVisitor()
    result.visit(suite_visitor)

    suites_with_tests = suite_visitor.suites_with_tests

    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    print("exporting data to database")

    session.add(TestRun(
            result.suite.name,
            result.statistics.total.passed,
            result.statistics.total.failed,
            result.statistics.total.skipped,
            result.statistics.total.total,
            result.suite.elapsed_time.total_seconds(),
            result.suite.start_time,
            result.suite.end_time
        )
    )

    for suite in suites_with_tests:
        session.add(TestSuite(
                (session.query(func.max(TestRun.id))[0][0]),
                suite.name,
                suite.statistics.passed,
                suite.statistics.failed,
                suite.statistics.skipped,
                suite.statistics.total,
                suite.elapsed_time.total_seconds(),
                suite.start_time,
                suite.end_time,
            )
        )
        for test in suite.tests:
            session.add(TestResults(
                    (session.query(func.max(TestSuite.id))[0][0]),
                    test.name,
                    test.status,
                    test.elapsed_time.total_seconds(),
                    test.start_time,
                    test.end_time,
                )
            )

            session.add(TestResultsJSON(
                    (session.query(func.max(TestResults.id))[0][0]),
                    ([test.to_dict()])

                )
            )    
    session.commit()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/output.xml")
    parser.add_argument("--retention_period", nargs='?', const='')
    args = parser.parse_args()
    return args

def remove_old_data(retention_period):
    if not retention_period:
        return
    else:
        print(f'removing data older than {retention_period}')
        test_results_json = f"delete from test_results_json where testresultid in(select id from test_results where testsuiteid in(select id from suite_results where testrunid in(select id from testrun_results where starttime <= now() - INTERVAL '{retention_period}')))" 
        test_results = f"delete from test_results where testsuiteid in(select id from suite_results where testrunid in(select id from testrun_results where starttime <= now() - INTERVAL '{retention_period}'))"
        suite_results = f"delete from suite_results where testrunid in(select id from testrun_results where starttime <= now() - INTERVAL '{retention_period}')"
        testrun_results = f"delete from testrun_results where starttime <= now() - INTERVAL '{retention_period}'"

    with engine.begin() as conn:
        conn.execute(text(test_results_json))
        conn.execute(text(test_results))
        conn.execute(text(suite_results))
        conn.execute(text(testrun_results))
    conn.commit()        

def main():
    inputs = parse_args()
    upload_results(input=inputs.input)
    remove_old_data(retention_period=inputs.retention_period)

if __name__ == "__main__":
    main()
